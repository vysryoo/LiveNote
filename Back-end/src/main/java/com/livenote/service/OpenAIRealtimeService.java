package com.livenote.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class OpenAIRealtimeService {
    private static final String REALTIME_API_URL = "wss://api.openai.com/v1/realtime";
    private static final String REALTIME_MODEL = "gpt-4o-realtime-preview-2024-10-01";
    private static final String TRANSCRIPTION_MODEL = "gpt-4o-transcribe";
    
    @Value("${openai.api-key}")
    private String apiKey;
    
    private final ObjectMapper objectMapper;
    private final OkHttpClient httpClient;

    public OpenAIRealtimeService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(0, TimeUnit.SECONDS) // WebSocket은 무한 타임아웃
                .writeTimeout(0, TimeUnit.SECONDS)
                .build();
    }

    public WebSocket createRealtimeConnection(String language, WebSocketListener listener) {
        try {
            // OpenAI Realtime API WebSocket 연결
            String url = REALTIME_API_URL + "?model=" + REALTIME_MODEL;
            
            Request request = new Request.Builder()
                    .url(url)
                    .addHeader("Authorization", "Bearer " + apiKey)
                    .addHeader("OpenAI-Beta", "realtime=v1")
                    .build();

            WebSocket webSocket = httpClient.newWebSocket(request, listener);
            
            // 연결 후 세션 설정 메시지 전송
            String languageCode = mapLanguageToCode(language);
            ObjectNode sessionUpdate = objectMapper.createObjectNode();
            sessionUpdate.put("type", "session.update");
            
            ObjectNode session = objectMapper.createObjectNode();
            session.set("modalities", objectMapper.createArrayNode().add("audio").add("text"));
            session.put("instructions", "You are a real-time transcription assistant. Transcribe the audio accurately.");
            
            // input_audio_format은 문자열로 지정 (pcm16은 24kHz mono 기본값)
            session.put("input_audio_format", "pcm16");
            
            // 오디오 출력은 사용하지 않으므로 output_audio_format 설정 제거
            
            ObjectNode transcription = objectMapper.createObjectNode();
            transcription.put("model", TRANSCRIPTION_MODEL);
            transcription.put("language", languageCode);
            session.set("input_audio_transcription", transcription);
            
            sessionUpdate.set("session", session);
            
            // 약간의 지연 후 세션 설정 전송 (연결이 완전히 설정된 후)
            new Thread(() -> {
                try {
                    Thread.sleep(100);
                    webSocket.send(sessionUpdate.toString());
                    log.info("OpenAI 세션 설정 완료: language={}", languageCode);
                } catch (Exception e) {
                    log.error("세션 설정 전송 실패", e);
                }
            }).start();
            
            return webSocket;
        } catch (Exception e) {
            log.error("OpenAI Realtime API 연결 실패", e);
            throw new RuntimeException("OpenAI Realtime API 연결 실패: " + e.getMessage(), e);
        }
    }

    public String mapLanguageToCode(String language) {
        // 프론트엔드에서 받은 언어를 OpenAI 언어 코드로 변환
        if (language == null) {
            return "ko";
        }
        
        return switch (language.toLowerCase()) {
            case "한국어", "korean", "ko" -> "ko";
            case "english", "영어", "en" -> "en";
            case "日本語", "japanese", "ja" -> "ja";
            case "汉语", "chinese", "중국어", "zh" -> "zh";
            default -> "ko"; // 기본값
        };
    }
}

