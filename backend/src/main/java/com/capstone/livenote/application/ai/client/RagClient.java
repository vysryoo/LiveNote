package com.capstone.livenote.application.ai.client;

import com.capstone.livenote.application.ai.dto.AiRequestPayloads;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.util.Assert;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI 서버(FastAPI) RAG 연동 클라이언트
 */
@Component
@RequiredArgsConstructor
public class RagClient {

    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    @Value("${ai.server.url:${app.ai.base-url}}")
    private String baseUrl;

    @Value("${app.callback-base-url}")
    private String callbackBaseUrl;

    private String callback(String type) {
        return callbackBaseUrl + "/api/ai/callback?type=" + type;
    }

    public void requestQnaGeneration(AiRequestPayloads.QnaGeneratePayload payload) {
        Map<String, Object> body = new HashMap<>();
        body.put("lectureId", payload.getLectureId());
        body.put("summaryId", payload.getSummaryId());
        body.put("sectionIndex", payload.getSectionIndex());
        body.put("sectionSummary", payload.getSectionSummary());
        body.put("subject", payload.getSubject());
        body.put("previousQa", payload.getPreviousQa());
        body.put("callbackUrl", callback("qna"));

        webClient.post()
                .uri(baseUrl + "/qa/generate")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    public void requestResourceRecommendation(AiRequestPayloads.ResourceRecommendPayload payload) {
        Map<String, Object> body = new HashMap<>();
        body.put("lectureId", payload.getLectureId());
        body.put("summaryId", payload.getSummaryId());
        body.put("sectionIndex", payload.getSectionIndex());
        body.put("sectionSummary", payload.getSectionSummary());
        body.put("previousSummaries", payload.getPreviousSummaries());
        body.put("ytExclude", payload.getYtExclude());
        body.put("wikiExclude", payload.getWikiExclude());
        body.put("paperExclude", payload.getPaperExclude());
        body.put("googleExclude", payload.getGoogleExclude());
        body.put("callbackUrl", callback("resources"));

        webClient.post()
                .uri(baseUrl + "/rec/recommend")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    public void upsertSummaryText(Long lectureId, Summary summary) {
        Assert.notNull(summary, "summary is required");
        Map<String, Object> metadata = Map.of(
                "summaryId", summary.getId(),
                "sectionIndex", summary.getSectionIndex(),
                "startSec", summary.getStartSec(),
                "endSec", summary.getEndSec()
        );

        Map<String, Object> item = new HashMap<>();
        item.put("text", summary.getText());
        item.put("id", summary.getId() != null ? summary.getId().toString() : null);
        item.put("section_id", summary.getSectionIndex());
        item.put("metadata", metadata);

        Map<String, Object> body = Map.of(
                "lecture_id", lectureId.toString(),
                "items", List.of(item)
        );

        webClient.post()
                .uri(baseUrl + "/rag/text-upsert")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    public void upsertPdf(Long lectureId, MultipartFile pdfFile, Map<String, Object> metadata) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("lecture_id", lectureId.toString());
        builder.part("file", pdfFile.getResource()).filename(pdfFile.getOriginalFilename());
        if (metadata != null && !metadata.isEmpty()) {
            builder.part("base_metadata", toJson(metadata));
        }

        webClient.post()
                .uri(baseUrl + "/rag/pdf-upsert")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(builder.build()))
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    private String toJson(Map<String, Object> metadata) {
        try {
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("failed to serialize metadata", e);
        }
    }
}
