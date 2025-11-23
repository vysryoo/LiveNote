package com.capstone.livenote.application.ai.client;

import com.capstone.livenote.application.ai.dto.AiRequestPayloads;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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
@Slf4j
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

        String url = baseUrl + "/qa/generate";
        log.info("🤖 [AI Server Call] QnA Generation Request:");
        log.info("   └─ URL: POST {}", url);
        log.info("   └─ lectureId: {}", payload.getLectureId());
        log.info("   └─ summaryId: {}", payload.getSummaryId());
        log.info("   └─ sectionIndex: {}", payload.getSectionIndex());
        log.info("   └─ subject: {}", payload.getSubject());
        log.info("   └─ sectionSummary length: {} chars", 
                payload.getSectionSummary() != null ? payload.getSectionSummary().length() : 0);
        log.info("   └─ previousQa count: {}", 
                payload.getPreviousQa() != null ? payload.getPreviousQa().size() : 0);
        log.info("   └─ callbackUrl: {}", callback("qna"));

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Server Call] QnA request sent successfully");
        } catch (Exception e) {
            log.error("❌ [AI Server Call] QnA request failed: {}", e.getMessage(), e);
            throw e;
        }
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

        String url = baseUrl + "/rec/recommend";
        log.info("🤖 [AI Server Call] Resource Recommendation Request:");
        log.info("   └─ URL: POST {}", url);
        log.info("   └─ lectureId: {}", payload.getLectureId());
        log.info("   └─ summaryId: {}", payload.getSummaryId());
        log.info("   └─ sectionIndex: {}", payload.getSectionIndex());
        log.info("   └─ sectionSummary length: {} chars", 
                payload.getSectionSummary() != null ? payload.getSectionSummary().length() : 0);
        log.info("   └─ previousSummaries count: {}", 
                payload.getPreviousSummaries() != null ? payload.getPreviousSummaries().size() : 0);
        log.info("   └─ excludes: yt={}, wiki={}, paper={}, google={}",
                payload.getYtExclude() != null ? payload.getYtExclude().size() : 0,
                payload.getWikiExclude() != null ? payload.getWikiExclude().size() : 0,
                payload.getPaperExclude() != null ? payload.getPaperExclude().size() : 0,
                payload.getGoogleExclude() != null ? payload.getGoogleExclude().size() : 0);
        log.info("   └─ callbackUrl: {}", callback("resources"));

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Server Call] Resource request sent successfully");
        } catch (Exception e) {
            log.error("❌ [AI Server Call] Resource request failed: {}", e.getMessage(), e);
            throw e;
        }
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

        String url = baseUrl + "/rag/text-upsert";
        log.info("🤖 [AI Server Call] RAG Text Upsert Request:");
        log.info("   └─ URL: POST {}", url);
        log.info("   └─ lectureId: {}", lectureId);
        log.info("   └─ summaryId: {}", summary.getId());
        log.info("   └─ sectionIndex: {}", summary.getSectionIndex());
        log.info("   └─ startSec: {}, endSec: {}", summary.getStartSec(), summary.getEndSec());
        log.info("   └─ text length: {} chars", 
                summary.getText() != null ? summary.getText().length() : 0);

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Server Call] RAG text upsert completed successfully");
        } catch (Exception e) {
            log.error("❌ [AI Server Call] RAG text upsert failed: {}", e.getMessage(), e);
            throw e;
        }
    }

    public void upsertPdf(Long lectureId, MultipartFile pdfFile, Map<String, Object> metadata) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("lecture_id", lectureId.toString());
        builder.part("file", pdfFile.getResource()).filename(pdfFile.getOriginalFilename());
        if (metadata != null && !metadata.isEmpty()) {
            builder.part("base_metadata", toJson(metadata));
        }

        String url = baseUrl + "/rag/pdf-upsert";
        log.info("🤖 [AI Server Call] RAG PDF Upsert Request:");
        log.info("   └─ URL: POST {}", url);
        log.info("   └─ lectureId: {}", lectureId);
        log.info("   └─ filename: {}", pdfFile.getOriginalFilename());
        log.info("   └─ fileSize: {} bytes", pdfFile.getSize());
        log.info("   └─ metadata: {}", metadata != null ? metadata.keySet() : "none");

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Server Call] PDF upsert completed successfully");
        } catch (Exception e) {
            log.error("❌ [AI Server Call] PDF upsert failed: {}", e.getMessage(), e);
            throw e;
        }
    }

    private String toJson(Map<String, Object> metadata) {
        try {
            return objectMapper.writeValueAsString(metadata);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("failed to serialize metadata", e);
        }
    }
}
