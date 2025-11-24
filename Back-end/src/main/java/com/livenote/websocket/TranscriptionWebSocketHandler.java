package com.livenote.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.livenote.entity.Lecture;
import com.livenote.entity.Transcript;
import com.livenote.entity.Summary;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.TranscriptRepository;
import com.livenote.repository.SummaryRepository;
import com.livenote.service.OpenAIRealtimeService;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.WebSocket;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@RequiredArgsConstructor
public class TranscriptionWebSocketHandler implements WebSocketHandler {
    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final SummaryRepository summaryRepository;
    private final OpenAIRealtimeService openAIRealtimeService;
    private final ObjectMapper objectMapper;
    
    // 세션별 오디오 버퍼 저장
    private final Map<String, ByteArrayOutputStream> audioBuffers = new ConcurrentHashMap<>();
    // 세션별 강의 ID 저장
    private final Map<String, Long> sessionLectureMap = new ConcurrentHashMap<>();
    // 세션별 섹션 인덱스 추적
    private final Map<String, Integer> sessionSectionMap = new ConcurrentHashMap<>();
    // 세션별 OpenAI WebSocket 연결
    private final Map<String, WebSocket> openAIWebSocketMap = new ConcurrentHashMap<>();
    // 세션별 언어 설정
    private final Map<String, String> sessionLanguageMap = new ConcurrentHashMap<>();
    // 강의 ID별 WebSocket 세션 저장 (같은 강의에 여러 세션이 있을 수 있으므로 List)
    private final Map<Long, java.util.List<WebSocketSession>> lectureSessionMap = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        String sessionId = session.getId();
        String query = session.getUri() != null ? session.getUri().getQuery() : null;
        
        log.info("WebSocket 연결 시도: sessionId={}, query={}", sessionId, query);
        
        try {
            if (query != null && query.contains("sessionId=")) {
                String lectureIdStr = query.substring(query.indexOf("sessionId=") + 10);
                try {
                    Long lectureId = Long.parseLong(lectureIdStr);
                    
                    Lecture lecture = lectureRepository.findById(lectureId)
                            .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다: " + lectureId));
                    
                    String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";
                    
                    log.info("강의 정보 조회 성공: lectureId={}, language={}", lectureId, language);
                    
                    sessionLectureMap.put(sessionId, lectureId);
                    sessionSectionMap.put(sessionId, 0);
                    audioBuffers.put(sessionId, new ByteArrayOutputStream());
                    sessionLanguageMap.put(sessionId, language);
                    
                    // 강의 ID별 세션 매핑 추가
                    lectureSessionMap.computeIfAbsent(lectureId, k -> new java.util.concurrent.CopyOnWriteArrayList<>()).add(session);
                    
                    // OpenAI Realtime API 연결
                    try {
                        log.info("OpenAI Realtime API 연결 시도: sessionId={}, language={}", sessionId, language);
                        OpenAIRealtimeListener listener = new OpenAIRealtimeListener(session, objectMapper, lectureId, transcriptRepository);
                        WebSocket openAIWebSocket = openAIRealtimeService.createRealtimeConnection(language, listener);
                        openAIWebSocketMap.put(sessionId, openAIWebSocket);
                        log.info("OpenAI Realtime API 연결 성공: sessionId={}, language={}", sessionId, language);
                    } catch (Exception e) {
                        log.error("OpenAI Realtime API 연결 실패: sessionId={}", sessionId, e);
                        try {
                            ObjectNode errorMessage = objectMapper.createObjectNode();
                            errorMessage.put("type", "error");
                            ObjectNode data = objectMapper.createObjectNode();
                            data.put("error", "OpenAI 연결 실패: " + e.getMessage());
                            errorMessage.set("data", data);
                            session.sendMessage(new TextMessage(errorMessage.toString()));
                        } catch (IOException ioException) {
                            log.error("에러 메시지 전송 실패: sessionId={}", sessionId, ioException);
                        }
                        // OpenAI 연결 실패 시 세션 닫기
                        session.close(CloseStatus.SERVER_ERROR.withReason("OpenAI 연결 실패"));
                        return;
                    }
                    
                    log.info("WebSocket 연결 완료: sessionId={}, lectureId={}, language={}", sessionId, lectureId, language);
                } catch (NumberFormatException e) {
                    log.error("잘못된 강의 ID: sessionId={}, lectureIdStr={}", sessionId, lectureIdStr, e);
                    session.close(CloseStatus.BAD_DATA.withReason("잘못된 강의 ID"));
                } catch (RuntimeException e) {
                    log.error("강의 조회 실패: sessionId={}, lectureId={}, error={}", sessionId, lectureIdStr, e.getMessage(), e);
                    session.close(CloseStatus.SERVER_ERROR.withReason("강의를 찾을 수 없습니다: lectureId=" + lectureIdStr));
                }
            } else {
                log.error("세션 ID가 없습니다: sessionId={}, query={}", sessionId, query);
                session.close(CloseStatus.BAD_DATA.withReason("세션 ID가 필요합니다"));
            }
        } catch (Exception e) {
            log.error("WebSocket 연결 설정 중 예외 발생: sessionId={}", sessionId, e);
            try {
                session.close(CloseStatus.SERVER_ERROR.withReason("서버 오류: " + e.getMessage()));
            } catch (Exception closeException) {
                log.error("세션 종료 실패: sessionId={}", sessionId, closeException);
            }
        }
    }

    @Override
    public void handleMessage(WebSocketSession session, WebSocketMessage<?> message) throws Exception {
        String sessionId = session.getId();
        WebSocket openAIWebSocket = openAIWebSocketMap.get(sessionId);
        
        if (openAIWebSocket == null) {
            log.warn("OpenAI WebSocket이 연결되지 않음: sessionId={}", sessionId);
            return;
        }
        
        if (message instanceof BinaryMessage) {
            BinaryMessage binaryMessage = (BinaryMessage) message;
            ByteBuffer payload = binaryMessage.getPayload();
            
            // 오디오 데이터를 버퍼에 저장
            ByteArrayOutputStream buffer = audioBuffers.get(sessionId);
            if (buffer != null) {
                byte[] bytes = new byte[payload.remaining()];
                payload.get(bytes);
                buffer.write(bytes);
                
                // OpenAI Realtime API로 오디오 데이터 전송
                sendAudioToOpenAI(openAIWebSocket, bytes);
            }
        } else if (message instanceof TextMessage) {
            // 텍스트 메시지 처리 (필요시)
            String text = ((TextMessage) message).getPayload();
            log.debug("텍스트 메시지 수신: {}", text);
            
            // OpenAI로 텍스트 메시지 전달 (필요시)
            try {
                openAIWebSocket.send(text);
            } catch (Exception e) {
                log.error("텍스트 메시지 전송 실패", e);
            }
        }
    }

    private void sendAudioToOpenAI(WebSocket openAIWebSocket, byte[] audioData) {
        try {
            // OpenAI Realtime API는 base64 인코딩된 오디오 데이터를 요청
            String base64Audio = java.util.Base64.getEncoder().encodeToString(audioData);
            
            // input_audio_buffer.append 메시지 형식 (OpenAI Realtime API 스펙)
            ObjectNode audioMessage = objectMapper.createObjectNode();
            audioMessage.put("type", "input_audio_buffer.append");
            audioMessage.put("audio", base64Audio);
            
            openAIWebSocket.send(audioMessage.toString());
            
        } catch (Exception e) {
            log.error("오디오 데이터 전송 실패", e);
        }
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("WebSocket 전송 오류: sessionId={}", session.getId(), exception);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus closeStatus) throws Exception {
        String sessionId = session.getId();
        
        // OpenAI WebSocket 연결 종료
        WebSocket openAIWebSocket = openAIWebSocketMap.remove(sessionId);
        if (openAIWebSocket != null) {
            try {
                openAIWebSocket.close(1000, "Client disconnected");
            } catch (Exception e) {
                log.error("OpenAI WebSocket 종료 실패", e);
            }
        }
        
        // 리소스 정리
        Long lectureId = sessionLectureMap.remove(sessionId);
        audioBuffers.remove(sessionId);
        sessionSectionMap.remove(sessionId);
        sessionLanguageMap.remove(sessionId);
        
        // 강의 ID별 세션 매핑에서 제거
        if (lectureId != null) {
            boolean isLastSession = lectureSessionMap.computeIfPresent(lectureId, (k, sessions) -> {
                sessions.remove(session);
                return sessions.isEmpty() ? null : sessions;
            }) == null;
            
            // 마지막 세션이 종료되었고, 강의가 recording 상태인 경우 duration 업데이트
            if (isLastSession) {
                updateLectureDuration(lectureId);
            }
        }
        
        log.info("WebSocket 연결 종료: sessionId={}, status={}", sessionId, closeStatus);
    }
    
    /**
     * 강의의 duration을 transcripts/summaries 기반으로 업데이트
     */
    @Transactional
    private void updateLectureDuration(Long lectureId) {
        try {
            Lecture lecture = lectureRepository.findById(lectureId).orElse(null);
            if (lecture == null || lecture.getStatus() != Lecture.LectureStatus.recording) {
                return;
            }
            
            // transcripts에서 마지막 섹션의 endSec 찾기
            List<Transcript> transcripts = transcriptRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
            double maxEndSecFromTranscripts = transcripts.stream()
                    .filter(t -> t.getEndSec() != null)
                    .mapToDouble(Transcript::getEndSec)
                    .max()
                    .orElse(0.0);
            
            // summaries에서 마지막 섹션의 endSec 찾기
            List<Summary> summaries = summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
            double maxEndSecFromSummaries = summaries.stream()
                    .filter(s -> s.getEndSec() != null)
                    .mapToDouble(Summary::getEndSec)
                    .max()
                    .orElse(0.0);
            
            // 두 값 중 더 큰 값을 사용
            double maxEndSec = Math.max(maxEndSecFromTranscripts, maxEndSecFromSummaries);
            
            // duration이 없거나, 계산된 값이 더 크면 업데이트
            if (maxEndSec > 0) {
                long durationSeconds = Math.round(maxEndSec);
                if (lecture.getDuration() == null || durationSeconds > lecture.getDuration()) {
                    lecture.setDuration(durationSeconds);
                    lectureRepository.save(lecture);
                    log.info("강의 duration 업데이트: lectureId={}, duration={}초", lectureId, durationSeconds);
                }
            }
        } catch (Exception e) {
            log.error("강의 duration 업데이트 실패: lectureId={}", lectureId, e);
        }
    }

    @Override
    public boolean supportsPartialMessages() {
        return true;
    }
    
    /**
     * 특정 강의의 모든 WebSocket 세션에 메시지 전송
     */
    public void sendMessageToLecture(Long lectureId, String message) {
        java.util.List<WebSocketSession> sessions = lectureSessionMap.get(lectureId);
        if (sessions != null && !sessions.isEmpty()) {
            for (WebSocketSession session : sessions) {
                try {
                    if (session.isOpen()) {
                        session.sendMessage(new TextMessage(message));
                        log.debug("메시지 전송 성공: lectureId={}, sessionId={}", lectureId, session.getId());
                    } else {
                        log.debug("세션이 닫혀있음: lectureId={}, sessionId={}", lectureId, session.getId());
                    }
                } catch (Exception e) {
                    log.error("메시지 전송 실패: lectureId={}, sessionId={}", lectureId, session.getId(), e);
                }
            }
        } else {
            log.debug("해당 강의에 연결된 세션이 없음: lectureId={}", lectureId);
        }
    }
}

