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
import java.util.HashMap;
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
 * OpenAI Realtime API의 전사 전용 세션으로 중계하는 WebSocket 핸들러.
 *
 * 클라이언트 요청: /ws/transcription?sessionId=<lectureId>
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

    @Value("${OPENAI_API_KEY}")
    private String openAiApiKey;

    @Value("${app.openai.realtime.transcription-model:gpt-4o-transcribe}")
    private String transcriptionModel;

    @Value("${app.callback-base-url:http://localhost:8080}")
    private String callbackBaseUrl;

    @Value("${app.transcription.padding-seconds:1.5}")
    private double transcriptPaddingSeconds;

    @Value("${app.transcription.speed-multiplier:1.0}")
    private double transcriptSpeedMultiplier;

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

        SessionContext ctx = new SessionContext(
                session,
                lectureId,
                language,
                startFromSec,
                transcriptPaddingSeconds,
                transcriptSpeedMultiplier
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
                // 발화 구간 길이(초): speech_started ~ 현재까지
                int segmentSec = ctx.endActiveSegment();
                if (segmentSec <= 0) segmentSec = Math.max(1, content.trim().length() / 10); // 최소 1초 보정

                int startSec = ctx.lastTranscriptEndSec;
                int endSec = startSec + segmentSec;

                // TranscriptService를 통해 저장 -> SectionAggregationService.onNewTranscript() 자동 호출
                transcriptService.saveFromStt(ctx.lectureId, startSec, endSec, content.trim());

                ctx.lastTranscriptEndSec = endSec;
                ctx.spokenSeconds = endSec; // spoken 시간 누적

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
                sendError(ctx.clientSession, errMsg);
                return;
            }
            
            // input_audio_buffer.speech_started 이벤트
            if (type.equals("input_audio_buffer.speech_started")) {
                log.info("[RealtimeWS] Speech started lectureId={}", ctx.lectureId);
                ctx.transcriptBuffer.setLength(0); // 버퍼 초기화
                ctx.speechStartMillis = System.currentTimeMillis();
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
        private long speechStartMillis = -1;
        private int spokenSeconds; // 말한 시간 누적
        private final double paddingSeconds;
        private final double speedMultiplier;

        SessionContext(WebSocketSession clientSession, Long lectureId, String language, int startFromSec,
                       double paddingSeconds, double speedMultiplier) {
            this.clientSession = clientSession;
            this.lectureId = lectureId;
            this.language = language;
            this.baseSeconds = startFromSec;
            this.lastTranscriptEndSec = startFromSec;
            this.spokenSeconds = startFromSec;
            this.paddingSeconds = paddingSeconds;
            this.speedMultiplier = speedMultiplier;
        }
        
        int getElapsedSeconds() {
            int active = 0;
            if (speechStartMillis > 0) {
                active = (int) ((System.currentTimeMillis() - speechStartMillis) / 1000);
            }
            return spokenSeconds + active;
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

        int endActiveSegment() {
            if (speechStartMillis <= 0) return 0;
            long now = System.currentTimeMillis();
            double deltaSeconds = ((now - speechStartMillis) / 1000.0) * speedMultiplier;
            // 약간의 완충(+paddingSeconds) 후 올림하여 반올림 효과
            int delta = (int) Math.ceil(deltaSeconds + paddingSeconds);
            spokenSeconds += delta;
            speechStartMillis = -1;
            return delta;
        }
    }
}
