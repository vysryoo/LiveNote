package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.security.JwtTokenProvider;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.WebSocket;
import java.nio.ByteBuffer;
import java.time.Duration;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
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
 * 프론트 → 백엔드 바이너리 PCM(24kHz, mono) 전송을 받아
 * OpenAI Realtime API의 전사 전용 세션으로 중계하는 WebSocket 핸들러.
 *
 * 클라이언트 요청: /ws/transcription?sessionId=<lectureId>&token=<JWT>
 * - 브라우저 WebSocket은 헤더를 붙일 수 없어 로그인 토큰을 쿼리로 받음. 본인 강의가 아니면 연결을 끊음.
 * - BinaryMessage만 전송(PCM16). 서버가 Base64 인코딩 후 input_audio_buffer.append로 전달.
 * - OpenAI 결과 중 transcript 계열 이벤트를 {type:"transcript", data:{content,isFinal}}로 클라이언트에 전달.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class RealtimeTranscriptionWebSocketHandler extends AbstractWebSocketHandler {

    // 응답 생성 없이 받아 적기만 하는 전사 전용 세션
    private static final URI OPENAI_REALTIME_URI =
            URI.create("wss://api.openai.com/v1/realtime?intent=transcription");

    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final TranscriptService transcriptService;
    private final ObjectMapper objectMapper;
    private final JwtTokenProvider jwtTokenProvider;

    @Value("${app.openai.api.key}")
    private String openAiApiKey;

    @Value("${app.openai.realtime.transcription-model:gpt-transcribe}")
    private String transcriptionModel;

    private final Map<String, SessionContext> contexts = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        String lectureIdStr = getQueryParam(session, "sessionId");
        if (lectureIdStr == null) {
            sendErrorAndClose(session, "sessionId is required");
            return;
        }

        Long lectureId;
        try {
            lectureId = Long.parseLong(lectureIdStr);
        } catch (NumberFormatException e) {
            sendErrorAndClose(session, "sessionId must be a number");
            return;
        }

        Optional<Long> userId = jwtTokenProvider.findUserId(getQueryParam(session, "token"));
        if (userId.isEmpty()) {
            sendErrorAndClose(session, "unauthorized");
            return;
        }

        // 다른 사용자의 강의도 없는 강의와 같은 응답으로 처리해 존재 여부를 드러내지 않음
        Optional<Lecture> lectureOpt = lectureRepository.findByIdAndUserId(lectureId, userId.get());
        if (lectureOpt.isEmpty()) {
            sendErrorAndClose(session, "lecture not found");
            return;
        }
        Lecture lecture = lectureOpt.get();
        String language = lecture.getSttLanguage() == null ? "ko" : lecture.getSttLanguage();

        // 강의 재개 시 이전 최대 endSec 가져오기
        Integer maxEndSec = transcriptRepository.findMaxEndSecByLectureId(lectureId);
        int startFromSec = maxEndSec != null ? maxEndSec : 0;
        
        log.info("[RealtimeWS] Lecture resume info: lectureId={} startFromSec={}", lectureId, startFromSec);

        SessionContext ctx = new SessionContext(
                session,
                lectureId,
                language,
                startFromSec
        );
        contexts.put(session.getId(), ctx);

        connectOpenAi(ctx);
        log.info("[RealtimeWS] connected clientSessionId={} lectureId={} lang={} resumeFrom={}s",
                session.getId(), lectureId, language, startFromSec);
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) {
        SessionContext ctx = contexts.get(session.getId());
        if (ctx == null) {
            sendErrorAndClose(session, "session context missing");
            return;
        }
        byte[] bytes = toByteArray(message.getPayload());
        if (bytes.length == 0) {
            return;
        }
        ctx.enqueueAudio(bytes);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        log.warn("[RealtimeWS] transport error sessionId={} err={}", session.getId(), exception.getMessage());
        sendError(session, "transport error: " + exception.getMessage());
        closeSession(session, CloseStatus.SERVER_ERROR);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        SessionContext ctx = contexts.remove(session.getId());
        if (ctx != null) {
            // 녹음을 멈춘 순간 말하던 문장과 전사 중인 문장을 잃지 않도록, 남은 결과를 받은 뒤 OpenAI 연결을 닫음
            ctx.finishAfterClientClosed();
        }
        log.info("[RealtimeWS] closed sessionId={} code={}", session.getId(), status);
    }

    private void connectOpenAi(SessionContext ctx) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        CompletableFuture<WebSocket> future = client.newWebSocketBuilder()
                .header("Authorization", "Bearer " + openAiApiKey)
                .connectTimeout(Duration.ofSeconds(5))
                .buildAsync(OPENAI_REALTIME_URI, new OpenAiListener(ctx));

        future.whenComplete((ws, err) -> {
            if (err != null) {
                log.error("[RealtimeWS] OpenAI connect fail lectureId={} err={}", ctx.lectureId, err.getMessage());
                sendError(ctx.clientSession, "failed to connect OpenAI: " + err.getMessage());
                closeSession(ctx.clientSession, CloseStatus.SERVER_ERROR);
                return;
            }
            ctx.setOpenAiWebSocket(ws);
            log.info("[RealtimeWS] OpenAI connected lectureId={}", ctx.lectureId);
            ctx.flushPending();
        });
    }

    private void sendTranscript(SessionContext ctx, String content, boolean isFinal) {
        sendTranscript(ctx, content, isFinal, null);
    }

    private void sendTranscript(SessionContext ctx, String content, boolean isFinal, String itemId) {
        try {
            // 1. 클라이언트로 전송
            String json = objectMapper.writeValueAsString(
                    Map.of(
                            "type", "transcript",
                            "data", Map.of(
                                    "content", content,
                                    "isFinal", isFinal
                            )
                    )
            );
            // 녹음을 멈춘 뒤 도착한 결과는 브라우저 연결이 닫혀 있으므로 전송 없이 저장만 함
            if (ctx.clientSession.isOpen()) {
                ctx.clientSession.sendMessage(new TextMessage(json));
            }
            
            // 2. isFinal==true일 때 TranscriptService를 통해 저장 (요약 생성 트리거)
            if (isFinal && content != null && !content.trim().isEmpty()) {
                // 발화 구간: OpenAI가 알려 준 녹음 음성 안의 위치(ms)를 강의 전체 시각으로 바꿈
                long[] range = ctx.takeSpeechRange(itemId);
                int startSec = Math.max(ctx.baseSeconds + (int) (range[0] / 1000), ctx.lastTranscriptEndSec);
                int endSec = Math.max(ctx.baseSeconds + (int) Math.ceil(range[1] / 1000.0), startSec + 1);

                // TranscriptService를 통해 저장 -> SectionAggregationService.onNewTranscript() 자동 호출
                transcriptService.saveFromStt(ctx.lectureId, startSec, endSec, content.trim());

                ctx.lastTranscriptEndSec = endSec;

                log.info("[RealtimeWS] ✅ Transcript saved to DB via TranscriptService: lectureId={} startSec={} endSec={} text={}",
                        ctx.lectureId, startSec, endSec, 
                        content.length() > 50 ? content.substring(0, 50) + "..." : content);
            }
        } catch (Exception e) {
            log.warn("[RealtimeWS] send transcript failed sessionId={} err={}", ctx.clientSession.getId(), e.getMessage());
        }
    }

    private void sendError(WebSocketSession session, String message) {
        try {
            String json = objectMapper.writeValueAsString(
                    Map.of("type", "error", "data", Map.of("error", message))
            );
            session.sendMessage(new TextMessage(json));
        } catch (Exception ignored) {
        }
    }

    private void sendErrorAndClose(WebSocketSession session, String message) {
        sendError(session, message);
        closeSession(session, CloseStatus.BAD_DATA);
    }

    private void closeSession(WebSocketSession session, CloseStatus status) {
        try {
            session.close(status);
        } catch (Exception ignored) {
        }
    }

    private String getQueryParam(WebSocketSession session, String key) {
        URI uri = session.getUri();
        if (uri == null || uri.getQuery() == null) return null;
        String[] pairs = uri.getQuery().split("&");
        for (String pair : pairs) {
            String[] kv = pair.split("=", 2);
            if (kv.length == 2 && kv[0].equals(key)) {
                return kv[1];
            }
        }
        return null;
    }

    private byte[] toByteArray(ByteBuffer buffer) {
        byte[] arr = new byte[buffer.remaining()];
        buffer.get(arr);
        return arr;
    }

    private class OpenAiListener implements WebSocket.Listener {
        private final SessionContext ctx;

        OpenAiListener(SessionContext ctx) {
            this.ctx = ctx;
        }

        @Override
        public void onOpen(WebSocket webSocket) {
            try {
                webSocket.sendText(buildSessionConfig(ctx.language), true);
                log.info("[RealtimeWS] Sent transcription session.update model={} lang={}",
                        transcriptionModel, ctx.language);
            } catch (Exception e) {
                log.warn("[RealtimeWS] Failed to send session config: {}", e.getMessage());
            }
            webSocket.request(1);
        }

        @Override
        public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
            handleOpenAiText(ctx, data.toString());
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
            log.warn("[RealtimeWS] OpenAI error lectureId={} err={}", ctx.lectureId, error.getMessage());
            sendError(ctx.clientSession, "openai error: " + error.getMessage());
        }

        @Override
        public CompletionStage<?> onClose(WebSocket webSocket, int statusCode, String reason) {
            log.info("[RealtimeWS] OpenAI closed lectureId={} code={} reason={}", ctx.lectureId, statusCode, reason);
            return null;
        }
    }

    private void handleOpenAiText(SessionContext ctx, String text) {
        try {
            JsonNode root = objectMapper.readTree(text);
            String type = root.path("type").asText("");
            
            // 디버깅용 로그 추가
            log.debug("[RealtimeWS] Received event type: {} lectureId={}", type, ctx.lectureId);

            // 오류 이벤트
            if (type.equalsIgnoreCase("error") || root.has("error")) {
                String errMsg = root.path("error").path("message").asText(type.isEmpty() ? "openai error" : type);
                log.error("[RealtimeWS] OpenAI error: {} lectureId={}", errMsg, ctx.lectureId);
                if (ctx.clientSession.isOpen()) {
                    sendError(ctx.clientSession, errMsg);
                } else {
                    // 녹음 종료 후 보낸 commit이 실패하면(버퍼가 비어 있는 등) 더 기다릴 결과가 없음
                    ctx.speechActive = false;
                    ctx.closeIfDrained();
                }
                return;
            }
            
            // input_audio_buffer.speech_started 이벤트
            if (type.equals("input_audio_buffer.speech_started")) {
                log.info("[RealtimeWS] Speech started lectureId={} audioStartMs={}", ctx.lectureId, root.path("audio_start_ms").asText("-"));
                ctx.transcriptBuffer.setLength(0); // 버퍼 초기화
                ctx.speechActive = true;
                ctx.markSpeechStart(root.path("item_id").asText(""), root.path("audio_start_ms").asLong(-1));
                return;
            }

            if (type.equals("input_audio_buffer.speech_stopped")) {
                ctx.speechActive = false;
                log.info("[RealtimeWS] Speech stopped lectureId={} audioEndMs={}", ctx.lectureId, root.path("audio_end_ms").asText("-"));
                ctx.markSpeechEnd(root.path("item_id").asText(""), root.path("audio_end_ms").asLong(-1));
                return;
            }

            // 말한 구간이 확정되어 전사가 시작됨. completed 또는 failed가 올 때까지 대기 목록에 둠
            if (type.equals("input_audio_buffer.committed")) {
                ctx.speechActive = false;
                ctx.pendingItems.add(root.path("item_id").asText(""));
                return;
            }
            
            // conversation.item.input_audio_transcription.completed 이벤트 (Whisper 전사 결과)
            if (type.equals("conversation.item.input_audio_transcription.completed")) {
                String transcript = root.path("transcript").asText("");
                if (!transcript.isEmpty()) {
                    log.info("[RealtimeWS] Transcription completed: {} lectureId={}", transcript, ctx.lectureId);
                    sendTranscript(ctx, transcript, true, root.path("item_id").asText(""));
                    ctx.transcriptBuffer.setLength(0);
                }
                ctx.pendingItems.remove(root.path("item_id").asText(""));
                ctx.closeIfDrained();
                return;
            }
            
            // conversation.item.input_audio_transcription.failed 이벤트
            if (type.equals("conversation.item.input_audio_transcription.failed")) {
                JsonNode error = root.path("error");
                log.warn("[RealtimeWS] Transcription failed: {} lectureId={}", error, ctx.lectureId);
                ctx.pendingItems.remove(root.path("item_id").asText(""));
                ctx.closeIfDrained();
                return;
            }

            // 말하는 중인 문장의 부분 전사. 프론트 표시용이며 저장하지 않음
            if (type.equals("conversation.item.input_audio_transcription.delta")) {
                String delta = root.path("delta").asText("");
                if (!delta.isEmpty()) {
                    ctx.transcriptBuffer.append(delta);
                    sendTranscript(ctx, ctx.transcriptBuffer.toString(), false);
                }
            }

        } catch (Exception e) {
            log.warn("[RealtimeWS] parse OpenAI text failed lectureId={} err={}", ctx.lectureId, e.getMessage());
        }
    }

    private String buildSessionConfig(String language) throws Exception {
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

    private static class SessionContext {
        // 녹음 종료 후 남은 전사 결과를 기다리는 최대 시간
        private static final long DRAIN_TIMEOUT_SECONDS = 10;

        private final WebSocketSession clientSession;
        private final Long lectureId;
        private final String language;
        private final Queue<byte[]> pendingAudio = new ConcurrentLinkedQueue<>();
        private final AtomicBoolean openAiReady = new AtomicBoolean(false);
        private final StringBuilder transcriptBuffer = new StringBuilder();
        private volatile WebSocket openAiWebSocket;
        // OpenAI로 보내는 음성 형식(PCM16, 24kHz, 모노)의 1초당 바이트 수
        private static final long AUDIO_BYTES_PER_SECOND = 24000L * 2;

        private final int baseSeconds; // 재개 시 기준 시간(초)
        private int lastTranscriptEndSec;
        // 발화 항목별 녹음 음성 안의 시작·끝 위치(ms). 끝을 모르면 -1
        private final Map<String, long[]> speechRanges = new ConcurrentHashMap<>();
        private final AtomicLong audioBytesSent = new AtomicLong();
        private volatile boolean speechActive;
        private final Set<String> pendingItems = ConcurrentHashMap.newKeySet();
        private final AtomicBoolean clientClosed = new AtomicBoolean(false);
        private final AtomicBoolean openAiClosed = new AtomicBoolean(false);

        SessionContext(WebSocketSession clientSession, Long lectureId, String language, int startFromSec) {
            this.clientSession = clientSession;
            this.lectureId = lectureId;
            this.language = language;
            this.baseSeconds = startFromSec;
            this.lastTranscriptEndSec = startFromSec;
        }
        

        void setOpenAiWebSocket(WebSocket ws) {
            this.openAiWebSocket = ws;
            openAiReady.set(true);
            // OpenAI에 연결되기 전에 녹음이 끝났으면 열린 연결이 남지 않도록 바로 닫음
            if (openAiClosed.get()) {
                try { ws.sendClose(WebSocket.NORMAL_CLOSURE, "client closed"); } catch (Exception ignored) {}
            }
        }

        void enqueueAudio(byte[] bytes) {
            if (openAiReady.get() && openAiWebSocket != null) {
                sendAudio(bytes);
            } else {
                pendingAudio.add(bytes);
            }
        }

        void flushPending() {
            if (!openAiReady.get() || openAiWebSocket == null) return;
            byte[] data;
            while ((data = pendingAudio.poll()) != null) {
                sendAudio(data);
            }
        }

        void sendAudio(byte[] bytes) {
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

        void sendToOpenAi(String payload) {
            if (openAiWebSocket != null) {
                openAiWebSocket.sendText(payload, true);
            }
        }

        void close() {
            if (!openAiClosed.compareAndSet(false, true)) return;
            if (openAiWebSocket != null) {
                try { openAiWebSocket.sendClose(WebSocket.NORMAL_CLOSURE, "client closed"); } catch (Exception ignored) {}
            }
        }

        void finishAfterClientClosed() {
            clientClosed.set(true);
            if (speechActive && openAiWebSocket != null) {
                // 말하던 중이면 지금까지의 음성으로 전사를 확정하도록 요청
                try { sendToOpenAi("{\"type\":\"input_audio_buffer.commit\"}"); } catch (Exception e) { speechActive = false; }
            }
            if (isDrained()) {
                close();
                return;
            }
            CompletableFuture.delayedExecutor(DRAIN_TIMEOUT_SECONDS, TimeUnit.SECONDS).execute(this::close);
        }

        void closeIfDrained() {
            if (clientClosed.get() && isDrained()) {
                close();
            }
        }

        private boolean isDrained() {
            return !speechActive && pendingItems.isEmpty();
        }

        void markSpeechStart(String itemId, long audioStartMs) {
            speechRanges.put(itemId, new long[]{audioStartMs >= 0 ? audioStartMs : sentAudioMs(), -1});
        }

        void markSpeechEnd(String itemId, long audioEndMs) {
            long[] range = speechRanges.get(itemId);
            if (range != null && audioEndMs >= 0) {
                range[1] = audioEndMs;
            }
        }

        // 발화의 녹음 음성 안 위치(ms)를 꺼낸다. 말 끝 이벤트 없이 확정된 발화(녹음 정지 시 강제 확정 등)는
        // 지금까지 보낸 음성 길이를 끝으로 보고, 위치를 모르는 발화는 직전 발화 끝부터로 봄
        long[] takeSpeechRange(String itemId) {
            long[] range = itemId == null ? null : speechRanges.remove(itemId);
            long fallbackStart = (long) (lastTranscriptEndSec - baseSeconds) * 1000;
            long start = range != null ? range[0] : fallbackStart;
            long end = range != null && range[1] >= 0 ? range[1] : sentAudioMs();
            return new long[]{start, Math.max(end, start)};
        }

        private long sentAudioMs() {
            return audioBytesSent.get() * 1000 / AUDIO_BYTES_PER_SECOND;
        }
    }
}
