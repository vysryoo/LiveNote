package com.capstone.livenote.application.ws;

import com.capstone.livenote.application.openai.service.OpenAiSttService;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket 오디오 스트리밍 핸들러
 *
 * 프론트엔드에서 실시간으로 오디오 청크를 WebSocket으로 전송하면
 * 1. OpenAI Whisper로 STT 처리
 * 2. Transcript 저장
 * 3. 30초마다 요약 생성
 * 4. AI 서버로 요약 전송
 * 5. 결과를 WebSocket으로 실시간 전송
 */
@Component
@RequiredArgsConstructor
public class AudioWebSocketHandler extends AbstractWebSocketHandler {

    private final OpenAiSttService sttService;
    private final TranscriptService transcriptService;
    private final LectureRepository lectureRepository;
    private final ObjectMapper objectMapper;

    // 세션별 강의 정보 저장
    private final Map<String, SessionInfo> sessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        System.out.println("[AudioWebSocket] 연결됨: " + session.getId());
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        JsonNode json = objectMapper.readTree(payload);
        String type = json.get("type").asText();

        if ("init".equals(type)) {
            // 초기화: 강의 ID 등록
            Long lectureId = json.get("lectureId").asLong();
            SessionInfo info = new SessionInfo(lectureId, 0);
            sessions.put(session.getId(), info);

            // 응답
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(Map.of(
                    "type", "init_ack",
                    "lectureId", lectureId,
                    "message", "WebSocket 초기화 완료"
            ))));

            System.out.println("[AudioWebSocket] 초기화: lectureId=" + lectureId);
        }
    }

    @Override
    protected void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        SessionInfo info = sessions.get(session.getId());
        if (info == null) {
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(Map.of(
                    "type", "error",
                    "message", "세션이 초기화되지 않았습니다. 먼저 init 메시지를 보내세요."
            ))));
            return;
        }

        try {
            // 1. 바이너리 데이터 추출
            byte[] audioData = message.getPayload().array();
            int chunkSeq = info.chunkSeq;
            int startSec = chunkSeq * 5; // 5초 단위 가정
            int endSec = startSec + 5;

            System.out.println("[AudioWebSocket] 오디오 수신: lectureId=" + info.lectureId +
                    " seq=" + chunkSeq + " size=" + audioData.length);

            // 2. 강의 언어 조회
            Lecture lecture = lectureRepository.findById(info.lectureId)
                    .orElseThrow(() -> new IllegalArgumentException("강의를 찾을 수 없습니다"));

            // 3. OpenAI Whisper STT 호출
            String filename = info.lectureId + "_" + chunkSeq + ".webm";
            String transcriptText = sttService.transcribe(audioData, filename, lecture.getSttLanguage());

            System.out.println("[AudioWebSocket] STT 완료: " +
                    transcriptText.substring(0, Math.min(50, transcriptText.length())));

            // 4. Transcript 저장 + 요약 트리거 + WebSocket 전송
            // (TranscriptService가 자동으로 StreamGateway를 통해 STOMP로 전송)
            transcriptService.saveFromStt(info.lectureId, startSec, endSec, transcriptText);

            // 5. 처리 완료 응답 (이 WebSocket 연결로도 ACK 전송)
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(Map.of(
                    "type", "chunk_ack",
                    "chunkSeq", chunkSeq,
                    "startSec", startSec,
                    "endSec", endSec
            ))));

            // 6. 다음 청크 시퀀스 증가
            info.chunkSeq++;

        } catch (Exception e) {
            System.err.println("[AudioWebSocket] 처리 오류: " + e.getMessage());
            session.sendMessage(new TextMessage(objectMapper.writeValueAsString(Map.of(
                    "type", "error",
                    "message", e.getMessage()
            ))));
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) throws Exception {
        SessionInfo info = sessions.remove(session.getId());
        if (info != null) {
            System.out.println("[AudioWebSocket] 연결 종료: lectureId=" + info.lectureId +
                    " 총 청크=" + info.chunkSeq);
        }
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        System.err.println("[AudioWebSocket] 전송 오류: " + exception.getMessage());
        sessions.remove(session.getId());
    }

    /**
     * 세션별 정보 저장 클래스
     */
    private static class SessionInfo {
        Long lectureId;
        int chunkSeq;

        SessionInfo(Long lectureId, int chunkSeq) {
            this.lectureId = lectureId;
            this.chunkSeq = chunkSeq;
        }
    }
}