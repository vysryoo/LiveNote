package com.capstone.livenote.application.openai.service;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.beans.factory.annotation.Value;


import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;


import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class OpenAiSummaryService {

    private final RestTemplate restTemplate;

    @Value("${OPENAI_API_KEY}")
    private String apiKey;


    private static final String GPT_URL = "https://api.openai.com/v1/chat/completions";
    private static final String MODEL = "gpt-4o-mini"; // 원하면 다른 모델명으로 변경

    public String summarize(String text) {

        try {
            // 1) 헤더
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.setBearerAuth(apiKey);

            // 2) 요청 바디
            Map<String, Object> body = Map.of(
                    "model", MODEL,
                    "temperature", 0.2,
                    "messages", List.of(
                            Map.of(
                                    "role", "system",
                                    "content", "당신은 강의 내용을 간결하게 요약하는 비서입니다. " +
                                            "사용자가 준 내용을 한국어로 3~5문장 정도로 핵심만 요약해 주세요."
                            ),
                            Map.of(
                                    "role", "user",
                                    "content", text
                            )
                    )
            );

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

            // 3) 호출
            Map<String, Object> response =
                    restTemplate.postForObject(GPT_URL, request, Map.class);

            if (response == null || !response.containsKey("choices")) {
                throw new RuntimeException("OpenAI 요약 응답이 비어 있습니다.");
            }

            List<Map<String, Object>> choices =
                    (List<Map<String, Object>>) response.get("choices");
            if (choices == null || choices.isEmpty()) {
                throw new RuntimeException("OpenAI 요약 응답에 choices가 없습니다.");
            }

            Map<String, Object> first = choices.get(0);
            Map<String, Object> message =
                    (Map<String, Object>) first.get("message");

            if (message == null || !message.containsKey("content")) {
                throw new RuntimeException("OpenAI 요약 응답에 message.content가 없습니다.");
            }

            String content = (String) message.get("content");
            return content != null ? content.trim() : "";

        } catch (Exception e) {
            System.err.println("[OpenAI SUMMARY 오류] " + e.getMessage());
            throw new RuntimeException("요약 생성 실패: " + e.getMessage(), e);
        }
    }
}

