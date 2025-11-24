package com.livenote.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.livenote.entity.Transcript;
import com.livenote.repository.TranscriptRepository;
import lombok.extern.slf4j.Slf4j;
import okhttp3.WebSocketListener;
import okio.ByteString;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;
import java.time.Instant;

@Slf4j
public class OpenAIRealtimeListener extends WebSocketListener {
    private final WebSocketSession clientSession;
    private final ObjectMapper objectMapper;
    private final Long lectureId;
    private final TranscriptRepository transcriptRepository;
    private final Instant sessionStartTime;
    
    public OpenAIRealtimeListener(WebSocketSession clientSession, ObjectMapper objectMapper, 
                                   Long lectureId, TranscriptRepository transcriptRepository) {
        this.clientSession = clientSession;
        this.objectMapper = objectMapper;
        this.lectureId = lectureId;
        this.transcriptRepository = transcriptRepository;
        this.sessionStartTime = Instant.now();
    }

    @Override
    public void onOpen(okhttp3.WebSocket webSocket, okhttp3.Response response) {
        log.info("OpenAI Realtime API 연결 성공");
        // 세션 설정은 OpenAIRealtimeService에서 처리
    }

    @Override
    public void onMessage(okhttp3.WebSocket webSocket, String text) {
        try {
            JsonNode message = objectMapper.readTree(text);
            String type = message.has("type") ? message.get("type").asText() : "unknown";
            
            log.debug("OpenAI 메시지 수신: type={}", type);
            
            // 전사 결과 처리 (OpenAI Realtime API 이벤트 타입)
            if ("conversation.item.input_audio_transcription.completed".equals(type)) {
                // 완료된 전사 결과
                JsonNode item = message.has("item") ? message.get("item") : message;
                String transcript = item.has("transcript") 
                    ? item.get("transcript").asText() 
                    : "";
                
                if (!transcript.isEmpty()) {
                    sendTranscriptToClient(transcript, true);
                }
            } else if ("response.audio_transcript.delta".equals(type)) {
                // 실시간 전사 델타 (부분 결과)
                String delta = message.has("delta") 
                    ? message.get("delta").asText() 
                    : "";
                
                if (!delta.isEmpty()) {
                    sendTranscriptToClient(delta, false);
                }
            } else if ("response.audio_transcript.done".equals(type)) {
                // 전사 완료
                log.info("전사 완료");
            } else if ("response.created".equals(type) && message.has("response")) {
                // 응답 생성 이벤트 처리
                JsonNode response = message.get("response");
                if (response.has("output")) {
                    JsonNode output = response.get("output");
                    if (output.isArray()) {
                        for (JsonNode item : output) {
                            if ("transcript".equals(item.get("type").asText())) {
                                String transcript = item.has("transcript") 
                                    ? item.get("transcript").asText() 
                                    : "";
                                if (!transcript.isEmpty()) {
                                    sendTranscriptToClient(transcript, true);
                                }
                            }
                        }
                    }
                }
            } else if ("error".equals(type)) {
                // 에러 처리
                String error = message.has("error") 
                    ? message.get("error").toString() 
                    : "Unknown error";
                log.error("OpenAI 에러: {}", error);
                sendErrorToClient(error);
            }
            
        } catch (Exception e) {
            log.error("OpenAI 메시지 처리 오류", e);
            sendErrorToClient(e.getMessage());
        }
    }
    
    private void sendTranscriptToClient(String transcript, boolean isFinal) {
        try {
            ObjectNode responseMessage = objectMapper.createObjectNode();
            responseMessage.put("type", "transcript");
            
            ObjectNode data = objectMapper.createObjectNode();
            data.put("content", transcript);
            data.put("isFinal", isFinal);
            responseMessage.set("data", data);
            
            clientSession.sendMessage(new TextMessage(responseMessage.toString()));
            
            // isFinal이 true일 때만 DB에 저장 (완료된 전사만 저장)
            if (isFinal && !transcript.isEmpty() && lectureId != null) {
                saveTranscriptToDatabase(transcript);
            }
        } catch (IOException e) {
            log.error("전사 결과 전송 실패", e);
        }
    }
    
    private void saveTranscriptToDatabase(String transcript) {
        try {
            // 현재 시간 기준으로 경과 시간 계산 (초 단위)
            long elapsedSeconds = Instant.now().getEpochSecond() - sessionStartTime.getEpochSecond();
            
            // 섹션 인덱스 계산 (30초 단위)
            int sectionIndex = (int) (elapsedSeconds / 30);
            
            // 섹션 시작/종료 시간 계산
            double startSec = sectionIndex * 30.0;
            double endSec = (sectionIndex + 1) * 30.0;
            
            // 전사 데이터 저장
            Transcript transcriptEntity = Transcript.builder()
                    .lectureId(lectureId)
                    .sectionIndex(sectionIndex)
                    .startSec(startSec)
                    .endSec(endSec)
                    .text(transcript)
                    .build();
            
            transcriptRepository.save(transcriptEntity);
            log.info("전사 데이터 DB 저장 완료: lectureId={}, sectionIndex={}, text=\"{}\"", 
                    lectureId, sectionIndex, transcript.length() > 50 ? transcript.substring(0, 50) + "..." : transcript);
        } catch (Exception e) {
            log.error("전사 데이터 DB 저장 실패: lectureId={}", lectureId, e);
        }
    }
    
    private void sendErrorToClient(String error) {
        try {
            ObjectNode errorMessage = objectMapper.createObjectNode();
            errorMessage.put("type", "error");
            
            ObjectNode data = objectMapper.createObjectNode();
            data.put("error", error);
            errorMessage.set("data", data);
            
            clientSession.sendMessage(new TextMessage(errorMessage.toString()));
        } catch (IOException e) {
            log.error("에러 메시지 전송 실패", e);
        }
    }

    @Override
    public void onMessage(okhttp3.WebSocket webSocket, ByteString bytes) {
        // 바이너리 메시지 처리 (필요시)
        log.debug("OpenAI 바이너리 메시지 수신: {} bytes", bytes.size());
    }

    @Override
    public void onClosing(okhttp3.WebSocket webSocket, int code, String reason) {
        log.info("OpenAI Realtime API 연결 종료: code={}, reason={}", code, reason);
        webSocket.close(1000, null);
    }

    @Override
    public void onClosed(okhttp3.WebSocket webSocket, int code, String reason) {
        log.info("OpenAI Realtime API 연결 완전 종료");
    }

    @Override
    public void onFailure(okhttp3.WebSocket webSocket, Throwable t, okhttp3.Response response) {
        log.error("OpenAI Realtime API 오류", t);
        try {
            ObjectNode errorMessage = objectMapper.createObjectNode();
            errorMessage.put("type", "error");
            
            ObjectNode data = objectMapper.createObjectNode();
            data.put("error", t.getMessage() != null ? t.getMessage() : "Unknown error");
            errorMessage.set("data", data);
            
            clientSession.sendMessage(new TextMessage(errorMessage.toString()));
        } catch (IOException e) {
            log.error("에러 메시지 전송 실패", e);
        }
    }
}

