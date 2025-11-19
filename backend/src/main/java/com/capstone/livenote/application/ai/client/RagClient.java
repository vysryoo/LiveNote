package com.capstone.livenote.application.ai.client;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

/**
 * AI 서버(FastAPI) RAG 연동 클라이언트
 */
@Component
@RequiredArgsConstructor
public class RagClient {

    private final WebClient webClient;

    @Value("${ai.server.url}")
    private String baseUrl;

    @Value("${app.callback-base-url}")
    private String callbackBaseUrl;

    private String callback(String type) {
        return callbackBaseUrl + "/api/ai/callback?type=" + type;
    }

    public void requestQnaGeneration(Long lectureId, Long summaryId, Integer sectionIndex) {
        var body = Map.of(
                "lectureId", lectureId,
                "summaryId", summaryId,
                "sectionIndex", sectionIndex,
                "callbackUrl", callback("qna")
        );

        webClient.post()
                .uri(baseUrl + "/qa/generate")
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    public void requestResourceRecommendation(Long lectureId, Long summaryId, Integer sectionIndex) {
        var body = Map.of(
                "lectureId", lectureId,
                "summaryId", summaryId,
                "sectionIndex", sectionIndex,
                "callbackUrl", callback("resources")
        );

        webClient.post()
                .uri(baseUrl + "/rec/recommend")
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }
}
