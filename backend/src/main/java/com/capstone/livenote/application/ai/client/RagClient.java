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

    @Value("${app.ai.base-url}")
    private String baseUrl;

    /**
     * Summary 텍스트를 RAG 인덱스에 업서트
     */
    public void upsertSummary(Long lectureId, Long summaryId, Integer sectionIndex, String text) {
        try {
            var body = Map.of(
                    "lectureId", lectureId,
                    "summaryId", summaryId,
                    "sectionIndex", sectionIndex,
                    "text", text
            );

            webClient.post()
                    .uri(baseUrl + "/rag/text-upsert")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();

            System.out.println("[RagClient] Summary upserted: summaryId=" + summaryId);

        } catch (Exception e) {
            System.err.println("[RagClient] RAG 업서트 실패: " + e.getMessage());
        }
    }

    /**
     * QnA 생성 요청
     */
    public void requestQnaGeneration(Long lectureId, Long summaryId, Integer sectionIndex) {
        try {
            var body = Map.of(
                    "lectureId", lectureId,
                    "summaryId", summaryId,
                    "sectionIndex", sectionIndex
            );

            webClient.post()
                    .uri(baseUrl + "/qa/generate")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();

            System.out.println("[RagClient] QnA generation requested: summaryId=" + summaryId);

        } catch (Exception e) {
            System.err.println("[RagClient] QnA 생성 요청 실패: " + e.getMessage());
        }
    }

    /**
     * 추천 자료 생성 요청
     */
    public void requestResourceRecommendation(Long lectureId, Long summaryId, Integer sectionIndex) {
        try {
            var body = Map.of(
                    "lectureId", lectureId,
                    "summaryId", summaryId,
                    "sectionIndex", sectionIndex
            );

            webClient.post()
                    .uri(baseUrl + "/rec/recommend")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();

            System.out.println("[RagClient] Resource recommendation requested: summaryId=" + summaryId);

        } catch (Exception e) {
            System.err.println("[RagClient] 추천 자료 요청 실패: " + e.getMessage());
        }
    }
}