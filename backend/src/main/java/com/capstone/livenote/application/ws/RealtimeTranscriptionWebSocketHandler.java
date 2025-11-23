package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
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
import java.util.Map;
import java.util.Optional;
import java.util.Queue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 프론트 → 백엔드 바이너리 PCM(24kHz, mono) 전송을 받아
 * OpenAI Realtime(gpt-4o-transcribe)로 중계하는 WebSocket 핸들러.
 *
 * 클라이언트 요청: /ws/transcription?sessionId=<lectureId>
 * - BinaryMessage만 전송(PCM16). 서버가 Base64 인코딩 후 input_audio_buffer.append로 전달.
 * - OpenAI 결과 중 transcript 계열 이벤트를 {type:"transcript", data:{content,isFinal}}로 클라이언트에 전달.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class RealtimeTranscriptionWebSocketHandler extends AbstractWebSocketHandler {

    private static final URI OPENAI_REALTIME_URI =
            URI.create("wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01");

    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final TranscriptService transcriptService;
    private final ObjectMapper objectMapper;

    @Value("${openai.api.key}")
    private String openAiApiKey;

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

        Optional<Lecture> lectureOpt = lectureRepository.findById(lectureId);
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

        SessionContext ctx = new SessionContext(session, lectureId, language, startFromSec);
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
            ctx.close();
        }
        log.info("[RealtimeWS] closed sessionId={} code={}", session.getId(), status);
    }

    private void connectOpenAi(SessionContext ctx) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        CompletableFuture<WebSocket> future = client.newWebSocketBuilder()
                .header("Authorization", "Bearer " + openAiApiKey)
                .header("OpenAI-Beta", "realtime=v1")
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
            ctx.clientSession.sendMessage(new TextMessage(json));
            
            // 2. isFinal==true일 때 TranscriptService를 통해 저장 (요약 생성 트리거)
            if (isFinal && content != null && !content.trim().isEmpty()) {
                int currentSec = ctx.getElapsedSeconds();
                int startSec = ctx.lastTranscriptEndSec;
                int endSec = currentSec;
                
                // TranscriptService를 통해 저장 -> SectionAggregationService.onNewTranscript() 자동 호출
                transcriptService.saveFromStt(ctx.lectureId, startSec, endSec, content.trim());
                
                ctx.lastTranscriptEndSec = currentSec;
                
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
            // OpenAI Realtime 세션 설정: 오디오 입력, 텍스트 출력, VAD 활성화
            try {
                String sessionConfig = """
                    {
                      "type": "session.update",
                      "session": {
                        "modalities": ["text"],
                        "instructions": "You are a helpful assistant that transcribes audio to text. Respond with transcriptions only.",
                        "voice": "alloy",
                        "input_audio_format": "pcm16",
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                          "model": "whisper-1"
                        },
                        "turn_detection": {
                          "type": "server_vad",
                          "threshold": 0.5,
                          "prefix_padding_ms": 300,
                          "silence_duration_ms": 500
                        },
                        "tools": [],
                        "tool_choice": "none",
                        "temperature": 0.8,
                        "max_response_output_tokens": "inf"
                      }
                    }
                    """;
                webSocket.sendText(sessionConfig, true);
                log.info("[RealtimeWS] Sent session.update with audio input enabled");
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
                sendError(ctx.clientSession, errMsg);
                return;
            }
            
            // input_audio_buffer.speech_started 이벤트
            if (type.equals("input_audio_buffer.speech_started")) {
                log.info("[RealtimeWS] Speech started lectureId={}", ctx.lectureId);
                ctx.transcriptBuffer.setLength(0); // 버퍼 초기화
                return;
            }
            
            // conversation.item.input_audio_transcription.completed 이벤트 (Whisper 전사 결과)
            if (type.equals("conversation.item.input_audio_transcription.completed")) {
                String transcript = root.path("transcript").asText("");
                if (!transcript.isEmpty()) {
                    log.info("[RealtimeWS] Transcription completed: {} lectureId={}", transcript, ctx.lectureId);
                    sendTranscript(ctx, transcript, true);
                    ctx.transcriptBuffer.setLength(0);
                }
                return;
            }
            
            // conversation.item.input_audio_transcription.failed 이벤트
            if (type.equals("conversation.item.input_audio_transcription.failed")) {
                JsonNode error = root.path("error");
                log.warn("[RealtimeWS] Transcription failed: {} lectureId={}", error, ctx.lectureId);
                return;
            }

            // delta / done 처리 (가능한 이벤트 다양성을 커버)
            if (type.contains("output_text.delta") || type.contains("audio_transcript.delta")) {
                String delta = extractDelta(root);
                if (!delta.isEmpty()) {
                    ctx.transcriptBuffer.append(delta);
                    sendTranscript(ctx, ctx.transcriptBuffer.toString(), false);
                }
                return;
            }

            if (type.contains("output_text.done") || type.contains("audio_transcript.done") || type.contains("response.done")) {
                String finalText = ctx.transcriptBuffer.toString();
                if (!finalText.isEmpty()) {
                    sendTranscript(ctx, finalText, true);
                    ctx.transcriptBuffer.setLength(0);
                }
                return;
            }

            // 기타 타입: response.output_text 혹은 transcript가 바로 content에 있을 경우
            if (root.has("content")) {
                String content = root.path("content").asText("");
                if (!content.isEmpty()) {
                    ctx.transcriptBuffer.append(content);
                    sendTranscript(ctx, ctx.transcriptBuffer.toString(), true);
                    ctx.transcriptBuffer.setLength(0);
                }
            }
        } catch (Exception e) {
            log.warn("[RealtimeWS] parse OpenAI text failed lectureId={} err={}", ctx.lectureId, e.getMessage());
        }
    }

    private String extractDelta(JsonNode root) {
        // 우선순위: delta 필드, text 필드, content 배열
        if (root.has("delta")) {
            JsonNode delta = root.get("delta");
            if (delta.isTextual()) return delta.asText("");
        }
        if (root.has("text") && root.get("text").isTextual()) {
            return root.get("text").asText("");
        }
        if (root.has("content") && root.get("content").isArray()) {
            StringBuilder sb = new StringBuilder();
            root.get("content").forEach(n -> {
                if (n.isTextual()) sb.append(n.asText());
            });
            return sb.toString();
        }
        return "";
    }

    private static class SessionContext {
        private final WebSocketSession clientSession;
        private final Long lectureId;
        private final String language;
        private final Queue<byte[]> pendingAudio = new ConcurrentLinkedQueue<>();
        private final AtomicBoolean openAiReady = new AtomicBoolean(false);
        private final StringBuilder transcriptBuffer = new StringBuilder();
        private volatile WebSocket openAiWebSocket;
        private final long startTimeMillis = System.currentTimeMillis();
        private final int baseSeconds; // 재개 시 기준 시간(초)
        private int lastTranscriptEndSec;

        SessionContext(WebSocketSession clientSession, Long lectureId, String language, int startFromSec) {
            this.clientSession = clientSession;
            this.lectureId = lectureId;
            this.language = language;
            this.baseSeconds = startFromSec;
            this.lastTranscriptEndSec = startFromSec;
        }
        
        int getElapsedSeconds() {
            return baseSeconds + (int) ((System.currentTimeMillis() - startTimeMillis) / 1000);
        }

        void setOpenAiWebSocket(WebSocket ws) {
            this.openAiWebSocket = ws;
            openAiReady.set(true);
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
            if (openAiWebSocket != null) {
                try { openAiWebSocket.sendClose(WebSocket.NORMAL_CLOSURE, "client closed"); } catch (Exception ignored) {}
            }
        }
    }
}
