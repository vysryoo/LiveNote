package com.capstone.livenote.recording;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.WebSocketSession;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.ByteBuffer;
import java.time.Duration;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 브라우저 녹음 연결 하나에 대응하는 OpenAI Realtime 전사 세션.
 *
 * 받은 음성(PCM16, 24kHz, 모노)을 OpenAI로 보내고, OpenAI의 전사 이벤트를 받아 브라우저로 중계하며 확정된 문장을 저장한다.
 * 녹음을 멈춘 뒤에도 말하던 문장의 전사가 끝날 때까지(최대 {@link #DRAIN_TIMEOUT_SECONDS}초) 기다렸다가 OpenAI 연결을 닫는다.
 * 브라우저 연결 스레드와 OpenAI 수신 스레드가 같은 상태를 다루므로 공유 필드는 동시성 안전한 타입을 쓴다.
 */
@Slf4j
class OpenAiTranscriptionSession {

    // 응답 생성 없이 받아 적기만 하는 전사 전용 세션
    private static final URI OPENAI_REALTIME_URI =
            URI.create("wss://api.openai.com/v1/realtime?intent=transcription");
    // 녹음 종료 후 남은 전사 결과를 기다리는 최대 시간
    private static final long DRAIN_TIMEOUT_SECONDS = 10;
    // OpenAI로 보내는 음성 형식(PCM16, 24kHz, 모노)의 1초당 바이트 수
    private static final long AUDIO_BYTES_PER_SECOND = 24000L * 2;

    private final WebSocketSession clientSession;
    private final Long lectureId;
    private final String language;
    private final ObjectMapper objectMapper;
    private final TranscriptService transcriptService;
    private final String transcriptionModel;

    private final Queue<byte[]> pendingAudio = new ConcurrentLinkedQueue<>();
    private final AtomicBoolean openAiReady = new AtomicBoolean(false);
    private final StringBuilder transcriptBuffer = new StringBuilder();
    private volatile WebSocket openAiWebSocket;

    private final int baseSeconds; // 재개 시 기준 시간(초)
    private int lastTranscriptEndSec;
    // 발화 항목별 녹음 음성 안의 시작·끝 위치(ms). 끝을 모르면 -1
    private final Map<String, long[]> speechRanges = new ConcurrentHashMap<>();
    private final AtomicLong audioBytesSent = new AtomicLong();
    private volatile boolean speechActive;
    private final Set<String> pendingItems = ConcurrentHashMap.newKeySet();
    private final AtomicBoolean clientClosed = new AtomicBoolean(false);
    private final AtomicBoolean openAiClosed = new AtomicBoolean(false);

    OpenAiTranscriptionSession(WebSocketSession clientSession, Long lectureId, String language, int startFromSec,
                               ObjectMapper objectMapper, TranscriptService transcriptService,
                               String transcriptionModel) {
        this.clientSession = clientSession;
        this.lectureId = lectureId;
        this.language = language;
        this.baseSeconds = startFromSec;
        this.lastTranscriptEndSec = startFromSec;
        this.objectMapper = objectMapper;
        this.transcriptService = transcriptService;
        this.transcriptionModel = transcriptionModel;
    }

    /**
     * OpenAI Realtime에 비동기로 연결한다. 연결 전에 받은 음성은 보관했다가 연결되면 보낸다.
     *
     * @param apiKey OpenAI API 키
     */
    void connect(String apiKey) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        CompletableFuture<WebSocket> future = client.newWebSocketBuilder()
                .header("Authorization", "Bearer " + apiKey)
                .connectTimeout(Duration.ofSeconds(5))
                .buildAsync(OPENAI_REALTIME_URI, new OpenAiListener());

        future.whenComplete((ws, err) -> {
            if (err != null) {
                log.error("[RealtimeWS] OpenAI connect fail lectureId={} err={}", lectureId, err.getMessage());
                ClientMessages.sendError(objectMapper, clientSession, "failed to connect OpenAI: " + err.getMessage());
                ClientMessages.close(clientSession, CloseStatus.SERVER_ERROR);
                return;
            }
            onOpenAiConnected(ws);
        });
    }

    void onOpenAiConnected(WebSocket ws) {
        this.openAiWebSocket = ws;
        openAiReady.set(true);
        // OpenAI에 연결되기 전에 녹음이 끝났으면 열린 연결이 남지 않도록 바로 닫음
        if (openAiClosed.get()) {
            try { ws.sendClose(WebSocket.NORMAL_CLOSURE, "client closed"); } catch (Exception ignored) {}
        }
        log.info("[RealtimeWS] OpenAI connected lectureId={}", lectureId);
        flushPending();
    }

    /**
     * 브라우저에서 받은 음성 조각을 OpenAI로 보낸다. 아직 연결 전이면 보관한다.
     *
     * @param bytes PCM16 음성
     */
    void appendAudio(byte[] bytes) {
        if (openAiReady.get() && openAiWebSocket != null) {
            sendAudio(bytes);
        } else {
            pendingAudio.add(bytes);
        }
    }

    /**
     * 브라우저 연결이 닫혔을 때 호출한다. 말하던 중이면 지금까지의 음성으로 전사를 확정하도록 요청하고,
     * 남은 전사 결과를 받은 뒤 OpenAI 연결을 닫는다.
     */
    void finishAfterClientClosed() {
        clientClosed.set(true);
        if (speechActive && openAiWebSocket != null) {
            try { sendToOpenAi("{\"type\":\"input_audio_buffer.commit\"}"); } catch (Exception e) { speechActive = false; }
        }
        if (isDrained()) {
            close();
            return;
        }
        CompletableFuture.delayedExecutor(DRAIN_TIMEOUT_SECONDS, TimeUnit.SECONDS).execute(this::close);
    }

    void handleEvent(String text) {
        try {
            JsonNode root = objectMapper.readTree(text);
            String type = root.path("type").asText("");

            log.debug("[RealtimeWS] Received event type: {} lectureId={}", type, lectureId);

            if (type.equalsIgnoreCase("error") || root.has("error")) {
                String errMsg = root.path("error").path("message").asText(type.isEmpty() ? "openai error" : type);
                log.error("[RealtimeWS] OpenAI error: {} lectureId={}", errMsg, lectureId);
                if (clientSession.isOpen()) {
                    ClientMessages.sendError(objectMapper, clientSession, errMsg);
                } else {
                    // 녹음 종료 후 보낸 commit이 실패하면(버퍼가 비어 있는 등) 더 기다릴 결과가 없음
                    speechActive = false;
                    closeIfDrained();
                }
                return;
            }

            if (type.equals("input_audio_buffer.speech_started")) {
                log.info("[RealtimeWS] Speech started lectureId={} audioStartMs={}", lectureId, root.path("audio_start_ms").asText("-"));
                transcriptBuffer.setLength(0);
                speechActive = true;
                markSpeechStart(root.path("item_id").asText(""), root.path("audio_start_ms").asLong(-1));
                return;
            }

            if (type.equals("input_audio_buffer.speech_stopped")) {
                speechActive = false;
                log.info("[RealtimeWS] Speech stopped lectureId={} audioEndMs={}", lectureId, root.path("audio_end_ms").asText("-"));
                markSpeechEnd(root.path("item_id").asText(""), root.path("audio_end_ms").asLong(-1));
                return;
            }

            // 말한 구간이 확정되어 전사가 시작됨. completed 또는 failed가 올 때까지 대기 목록에 둠
            if (type.equals("input_audio_buffer.committed")) {
                speechActive = false;
                pendingItems.add(root.path("item_id").asText(""));
                return;
            }

            if (type.equals("conversation.item.input_audio_transcription.completed")) {
                String transcript = root.path("transcript").asText("");
                if (!transcript.isEmpty()) {
                    log.info("[RealtimeWS] Transcription completed: {} lectureId={}", transcript, lectureId);
                    sendTranscript(transcript, true, root.path("item_id").asText(""));
                    transcriptBuffer.setLength(0);
                }
                pendingItems.remove(root.path("item_id").asText(""));
                closeIfDrained();
                return;
            }

            if (type.equals("conversation.item.input_audio_transcription.failed")) {
                JsonNode error = root.path("error");
                log.warn("[RealtimeWS] Transcription failed: {} lectureId={}", error, lectureId);
                pendingItems.remove(root.path("item_id").asText(""));
                closeIfDrained();
                return;
            }

            // 말하는 중인 문장의 부분 전사. 프론트 표시용이며 저장하지 않음
            if (type.equals("conversation.item.input_audio_transcription.delta")) {
                String delta = root.path("delta").asText("");
                if (!delta.isEmpty()) {
                    transcriptBuffer.append(delta);
                    sendTranscript(transcriptBuffer.toString(), false, null);
                }
            }

        } catch (Exception e) {
            log.warn("[RealtimeWS] parse OpenAI text failed lectureId={} err={}", lectureId, e.getMessage());
        }
    }

    private void sendTranscript(String content, boolean isFinal, String itemId) {
        try {
            // 녹음을 멈춘 뒤 도착한 결과는 브라우저 연결이 닫혀 있으므로 전송 없이 저장만 함
            if (clientSession.isOpen()) {
                ClientMessages.sendTranscript(objectMapper, clientSession, content, isFinal);
            }

            if (isFinal && content != null && !content.trim().isEmpty()) {
                // 발화 구간: OpenAI가 알려 준 녹음 음성 안의 위치(ms)를 강의 전체 시각으로 바꿈
                long[] range = takeSpeechRange(itemId);
                int startSec = Math.max(baseSeconds + (int) (range[0] / 1000), lastTranscriptEndSec);
                int endSec = Math.max(baseSeconds + (int) Math.ceil(range[1] / 1000.0), startSec + 1);

                transcriptService.saveFromStt(lectureId, startSec, endSec, content.trim());

                lastTranscriptEndSec = endSec;

                log.info("[RealtimeWS] Transcript saved: lectureId={} startSec={} endSec={} text={}",
                        lectureId, startSec, endSec,
                        content.length() > 50 ? content.substring(0, 50) + "..." : content);
            }
        } catch (Exception e) {
            log.warn("[RealtimeWS] send transcript failed sessionId={} err={}", clientSession.getId(), e.getMessage());
        }
    }

    private String buildSessionConfig() throws Exception {
        Map<String, Object> transcription = new HashMap<>();
        transcription.put("model", transcriptionModel);
        if (language != null && !language.isBlank()) {
            transcription.put("language", language);
        }
        Map<String, Object> config = Map.of(
                "type", "session.update",
                "session", Map.of(
                        "type", "transcription",
                        "audio", Map.of(
                                "input", Map.of(
                                        "format", Map.of("type", "audio/pcm", "rate", 24000),
                                        "transcription", transcription,
                                        "turn_detection", Map.of(
                                                "type", "server_vad",
                                                "threshold", 0.5,
                                                "prefix_padding_ms", 300,
                                                "silence_duration_ms", 500
                                        )
                                )
                        )
                )
        );
        return objectMapper.writeValueAsString(config);
    }

    private void flushPending() {
        if (!openAiReady.get() || openAiWebSocket == null) return;
        byte[] data;
        while ((data = pendingAudio.poll()) != null) {
            sendAudio(data);
        }
    }

    private void sendAudio(byte[] bytes) {
        if (openAiWebSocket == null) return;
        try {
            audioBytesSent.addAndGet(bytes.length);
            String b64 = Base64.getEncoder().encodeToString(bytes);
            String payload = "{\"type\":\"input_audio_buffer.append\",\"audio\":\"" + b64 + "\"}";
            openAiWebSocket.sendText(payload, true);
        } catch (Exception e) {
            // 클라이언트에 에러 전파는 상위에서 처리
        }
    }

    private void sendToOpenAi(String payload) {
        if (openAiWebSocket != null) {
            openAiWebSocket.sendText(payload, true);
        }
    }

    private void close() {
        if (!openAiClosed.compareAndSet(false, true)) return;
        if (openAiWebSocket != null) {
            try { openAiWebSocket.sendClose(WebSocket.NORMAL_CLOSURE, "client closed"); } catch (Exception ignored) {}
        }
    }

    private void closeIfDrained() {
        if (clientClosed.get() && isDrained()) {
            close();
        }
    }

    private boolean isDrained() {
        return !speechActive && pendingItems.isEmpty();
    }

    private void markSpeechStart(String itemId, long audioStartMs) {
        speechRanges.put(itemId, new long[]{audioStartMs >= 0 ? audioStartMs : sentAudioMs(), -1});
    }

    private void markSpeechEnd(String itemId, long audioEndMs) {
        long[] range = speechRanges.get(itemId);
        if (range != null && audioEndMs >= 0) {
            range[1] = audioEndMs;
        }
    }

    // 발화의 녹음 음성 안 위치(ms)를 꺼낸다. 말 끝 이벤트 없이 확정된 발화(녹음 정지 시 강제 확정 등)는
    // 지금까지 보낸 음성 길이를 끝으로 보고, 위치를 모르는 발화는 직전 발화 끝부터로 봄
    private long[] takeSpeechRange(String itemId) {
        long[] range = itemId == null ? null : speechRanges.remove(itemId);
        long fallbackStart = (long) (lastTranscriptEndSec - baseSeconds) * 1000;
        long start = range != null ? range[0] : fallbackStart;
        long end = range != null && range[1] >= 0 ? range[1] : sentAudioMs();
        return new long[]{start, Math.max(end, start)};
    }

    private long sentAudioMs() {
        return audioBytesSent.get() * 1000 / AUDIO_BYTES_PER_SECOND;
    }

    private class OpenAiListener implements WebSocket.Listener {

        @Override
        public void onOpen(WebSocket webSocket) {
            try {
                webSocket.sendText(buildSessionConfig(), true);
                log.info("[RealtimeWS] Sent transcription session.update model={} lang={}", transcriptionModel, language);
            } catch (Exception e) {
                log.warn("[RealtimeWS] Failed to send session config: {}", e.getMessage());
            }
            webSocket.request(1);
        }

        @Override
        public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
            handleEvent(data.toString());
            webSocket.request(1);
            return null;
        }

        @Override
        public CompletionStage<?> onBinary(WebSocket webSocket, ByteBuffer data, boolean last) {
            webSocket.request(1);
            return null; // 예상치 못한 바이너리는 무시
        }

        @Override
        public void onError(WebSocket webSocket, Throwable error) {
            log.warn("[RealtimeWS] OpenAI error lectureId={} err={}", lectureId, error.getMessage());
            ClientMessages.sendError(objectMapper, clientSession, "openai error: " + error.getMessage());
        }

        @Override
        public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
            log.info("[RealtimeWS] OpenAI closed lectureId={} code={} reason={}", lectureId, statusCode, reason);
            return null;
        }
    }
}
