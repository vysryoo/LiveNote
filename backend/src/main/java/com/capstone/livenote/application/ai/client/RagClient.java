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
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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

    // 1. QnA 생성 요청 (snake_case 적용)
    public void requestQnaGeneration(AiRequestPayloads.QnaGeneratePayload payload, List<String> targetTypes) {
        Map<String, Object> body = new HashMap<>();

        // 명세서 "예시 1" 및 "입력 필드 설명" 기준 매핑
        body.put("lecture_id", payload.getLectureId());       // lectureId -> lecture_id
        //body.put("lecture_id", String.valueOf(payload.getLectureId()));

        body.put("summary_id", payload.getSummaryId());       // summaryId -> summary_id
        body.put("section_index", payload.getSectionIndex()); // sectionIndex -> section_index
        body.put("section_summary", payload.getSectionSummary()); // sectionSummary -> section_summary

        body.put("subject", payload.getSubject());
        body.put("previous_qa", payload.getPreviousQa());     // previousQa -> previous_qa
        body.put("callback_url", callback("qna"));            // callbackUrl -> callback_url

        String url = baseUrl + "/qa/generate";

        log.info("🤖 [AI QnA] Request: lecture_id={} section_index={} callback={}",
                payload.getLectureId(), payload.getSectionIndex(), callback("qna"));

        if (targetTypes != null && !targetTypes.isEmpty()) {
            body.put("question_types", targetTypes);
        }

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI QnA] Request sent successfully");
        } catch (Exception e) {
            log.error("❌ [AI QnA] Request failed: {}", e.getMessage(), e);
            throw e;
        }
    }

    // 2. Resource 추천 요청 (snake_case + 실제 필드 둘 다 보내기)
    public void requestResourceRecommendation(AiRequestPayloads.ResourceRecommendPayload payload, List<String> targetTypes) {
        Map<String, Object> body = new HashMap<>();

        body.put("lecture_id", String.valueOf(payload.getLectureId()));
        body.put("section_id", payload.getSectionIndex() + 1);
        body.put("section_index", payload.getSectionIndex());
        body.put("section_summary", payload.getSectionSummary());

        // previous_summaries 변환
        List<Map<String, Object>> prev = payload.getPreviousSummaries().stream()
                .map(s -> {
                    Map<String, Object> m = new HashMap<>();
                    m.put("section_index", s.getSectionIndex());
                    m.put("section_id", s.getSectionIndex() + 1);
                    m.put("summary", s.getSummary());
                    return m;
                })
                .collect(Collectors.toList());
        body.put("previous_summaries", prev);

        body.put("yt_exclude", payload.getYtExclude());
        body.put("wiki_exclude", payload.getWikiExclude());
        body.put("paper_exclude", payload.getPaperExclude());
        body.put("google_exclude", payload.getGoogleExclude());

        body.put("callback_url", callback("resources"));

        String url = baseUrl + "/rec/recommend";

        log.info("🤖 [AI Resource] Request body = {}", body);

        if (targetTypes != null && !targetTypes.isEmpty()) {
            body.put("resource_types", targetTypes);
        }

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Resource] Request sent successfully");
        } catch (WebClientResponseException e) {
            // 🔥 AI 서버가 보낸 에러 응답 body 로그
            log.error("❌ [AI Resource] status={} body={}",
                    e.getStatusCode().value(),
                    e.getResponseBodyAsString());
            throw e;
        } catch (Exception e) {
            log.error("❌ [AI Resource] Request failed (non-HTTP error): {}", e.getMessage(), e);
            throw e;
        }
    }


    public void requestSummaryGeneration(Long lectureId,
                                         Long summaryId,
                                         Integer sectionIndex,
                                         Integer startSec,
                                         Integer endSec,
                                         String phase,          // "FINAL" 또는 "PARTIAL"
                                         String transcript) {

        Map<String, Object> body = new HashMap<>();
        body.put("lecture_id", lectureId);
        if (summaryId != null) {
            body.put("summary_id", summaryId);
        }
        body.put("section_index", sectionIndex);

        if (startSec != null) {
            body.put("start_sec", startSec);
        }
        if (endSec != null) {
            body.put("end_sec", endSec);
        }

        // 명세서: 기본값 FINAL, 대문자
        body.put("phase", phase != null ? phase.toUpperCase() : "FINAL");

        // string 또는 array[string] 둘 다 허용 → 우리는 일단 통짜 string 으로 보냄
        body.put("transcript", transcript);

        // 콜백 URL (type=summary 는 AI 서버가 자동으로 붙여 준다고 했지만
        // 우리도 /api/ai/callback?type=summary 로 맞춰 줌)
        body.put("callback_url", callback("summary"));

        String url = baseUrl + "/summary/generate";

        log.info("🤖 [AI Summary] Request body = {}", body);

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Summary] Request sent successfully");
        } catch (Exception e) {
            log.error("❌ [AI Summary] Request failed: {}", e.getMessage(), e);
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

        // ✅ id: null이면 아예 안 넣기
        if (summary.getId() != null) {
            item.put("id", summary.getId().toString());
        }

        // ✅ section_id 는 문자열로 보내기
        item.put("section_id", String.valueOf(summary.getSectionIndex()));
        item.put("metadata", metadata);

        Map<String, Object> body = new HashMap<>();
        body.put("lecture_id", String.valueOf(lectureId));
        body.put("items", List.of(item));

        String url = baseUrl + "/rag/text-upsert";

        log.info("🤖 [AI Server Call] RAG Text Upsert Request body = {}", body);

        try {
            webClient.post()
                    .uri(url)
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
            log.info("✅ [AI Server Call] RAG text upsert completed successfully");
        } catch (WebClientResponseException e) {
            // ✅ 어디서 터지는지 AI가 준 detail 까지 찍기
            log.error("❌ [AI Server Call] RAG text upsert failed: status={} body={}",
                    e.getStatusCode(), e.getResponseBodyAsString());
            throw e;
        } catch (Exception e) {
            log.error("❌ [AI Server Call] RAG text upsert failed: {}", e.getMessage(), e);
            throw e;
        }
    }


    public String upsertPdf(Long lectureId, MultipartFile pdfFile, Map<String, Object> metadata) {
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
            // [수정] 응답 본문을 받아서 collection_id 추출
            String responseBody = webClient.post()
                    .uri(url)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .bodyToMono(String.class) // String으로 받음
                    .block();

            log.info("✅ [AI Server Call] PDF upsert completed. Response: {}", responseBody);

            // 간단한 JSON 파싱 (Jackson 사용 가정)
            // {"collection_id": "lecture_1", "result": {...}}
            return objectMapper.readTree(responseBody).get("collection_id").asText();

        } catch (Exception e) {
            log.error("❌ [AI Server Call] PDF upsert failed: {}", e.getMessage(), e);
            throw new RuntimeException("RAG Upsert Failed", e);
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
