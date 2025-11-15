package com.capstone.livenote.application.openai.service;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

/**
 * OpenAI Whisper API를 사용한 STT 서비스
 */
@Service
@RequiredArgsConstructor
public class OpenAiSttService {

    @Value("${openai.api-key}")
    private String apiKey;

    @Value("${openai.stt.model:whisper-1}")
    private String model;

    private static final String WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions";

    private final RestTemplate restTemplate;

    /**
     * 오디오 파일을 텍스트로 변환
     */
    public String transcribe(byte[] audioBytes, String filename, String language) {
        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new ByteArrayResource(audioBytes) {
                @Override
                public String getFilename() {
                    return filename;
                }
            });
            body.add("model", model);
            body.add("language", language);
            body.add("response_format", "json");

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            headers.setBearerAuth(apiKey);

            HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

            Map<String, Object> response = restTemplate.postForObject(WHISPER_URL, request, Map.class);

            if (response != null && response.containsKey("text")) {
                return (String) response.get("text");
            }

            throw new RuntimeException("OpenAI STT 응답에 text 필드가 없습니다");

        } catch (Exception e) {
            System.err.println("[OpenAI STT 오류] " + e.getMessage());
            throw new RuntimeException("STT 처리 실패: " + e.getMessage(), e);
        }
    }
}