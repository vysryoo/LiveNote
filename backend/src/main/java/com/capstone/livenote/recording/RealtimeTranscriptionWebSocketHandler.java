package com.capstone.livenote.recording;

import com.capstone.livenote.lecture.Lecture;
import com.capstone.livenote.lecture.LectureRepository;
import com.capstone.livenote.global.security.JwtTokenProvider;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import java.net.URI;
import java.nio.ByteBuffer;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 프론트 → 백엔드 바이너리 PCM(24kHz, mono) 전송을 받아
 * OpenAI Realtime API의 전사 전용 세션으로 중계하는 WebSocket 핸들러.
 *
 * 클라이언트 요청: /ws/transcription?sessionId=<lectureId>&token=<JWT>
 * - 브라우저 WebSocket은 헤더를 붙일 수 없어 로그인 토큰을 쿼리로 받음. 본인 강의가 아니면 연결을 끊음.
 * - BinaryMessage만 전송(PCM16). OpenAI와 주고받는 처리는 연결마다 만드는 {@link OpenAiTranscriptionSession}이 맡음.
 * - OpenAI 결과 중 transcript 계열 이벤트를 {type:"transcript", data:{content,isFinal}}로 클라이언트에 전달.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class RealtimeTranscriptionWebSocketHandler extends AbstractWebSocketHandler {

    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final TranscriptService transcriptService;
    private final ObjectMapper objectMapper;
    private final JwtTokenProvider jwtTokenProvider;

    @Value("${app.openai.api.key}")
    private String openAiApiKey;

    @Value("${app.openai.realtime.transcription-model:gpt-transcribe}")
    private String transcriptionModel;

    private final Map<String, OpenAiTranscriptionSession> sessions = new ConcurrentHashMap<>();

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

        OpenAiTranscriptionSession transcription = new OpenAiTranscriptionSession(
                session, lectureId, language, startFromSec, objectMapper, transcriptService, transcriptionModel);
        sessions.put(session.getId(), transcription);

        transcription.connect(openAiApiKey);
        log.info("[RealtimeWS] connected clientSessionId={} lectureId={} lang={} resumeFrom={}s",
                session.getId(), lectureId, language, startFromSec);
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) {
        OpenAiTranscriptionSession transcription = sessions.get(session.getId());
        if (transcription == null) {
            sendErrorAndClose(session, "session context missing");
            return;
        }
        byte[] bytes = toByteArray(message.getPayload());
        if (bytes.length == 0) {
            return;
        }
        transcription.appendAudio(bytes);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        log.warn("[RealtimeWS] transport error sessionId={} err={}", session.getId(), exception.getMessage());
        ClientMessages.sendError(objectMapper, session, "transport error: " + exception.getMessage());
        ClientMessages.close(session, CloseStatus.SERVER_ERROR);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        OpenAiTranscriptionSession transcription = sessions.remove(session.getId());
        if (transcription != null) {
            // 녹음을 멈춘 순간 말하던 문장과 전사 중인 문장을 잃지 않도록, 남은 결과를 받은 뒤 OpenAI 연결을 닫음
            transcription.finishAfterClientClosed();
        }
        log.info("[RealtimeWS] closed sessionId={} code={}", session.getId(), status);
    }

    private void sendErrorAndClose(WebSocketSession session, String message) {
        ClientMessages.sendError(objectMapper, session, message);
        ClientMessages.close(session, CloseStatus.BAD_DATA);
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
}
