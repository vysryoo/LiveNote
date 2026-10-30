package com.capstone.livenote.ai;

import com.capstone.livenote.summary.Summary;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.capstone.livenote.global.security.InternalApiKey;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Component;
import org.springframework.util.Assert;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * AI 서버(FastAPI)에 요약, 자료 추천, QnA 생성, RAG 업서트를 요청한다.
 *
 * 모든 요청에 백엔드와 AI 서버가 공유하는 내부 키를 붙인다. 요약과 자료 추천 결과는 콜백으로 돌아온다.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class AiServerClient {

    private static final ParameterizedTypeReference<ServerSentEvent<String>> SSE_OF_STRING =
            new ParameterizedTypeReference<>() {};

    private final WebClient webClient;
    private final ObjectMapper objectMapper;
    private final InternalApiKey internalApiKey;

    @Value("${app.ai.base-url}")
    private String baseUrl;

    @Value("${app.callback-base-url}")
    private String callbackBaseUrl;

    private String callback(String type) {
        return callbackBaseUrl + "/api/ai/callback?type=" + type;
    }

    /**
     * AI 서버에 QnA 생성을 요청하고 생성 과정을 SSE 이벤트로 받는다.
     *
     * 반환한 Flux를 구독할 때 요청을 보낸다. 이벤트 종류는 start, question, answer, done, error이며
     * data는 JSON 문자열이다. AI 서버가 오류 상태 코드로 응답하면 Flux가 {@link WebClientResponseException}으로 끝난다.
     *
     * @param payload QnA 생성 요청 본문
     * @param targetTypes 생성할 질문 유형. null이거나 비어 있으면 AI 서버 설정값 사용
     * @return AI 서버가 보내는 SSE 이벤트
     */
    public Flux<ServerSentEvent<String>> streamQnaGeneration(AiRequestPayloads.QnaGeneratePayload payload, List<String> targetTypes) {
        Map<String, Object> body = new HashMap<>();

        body.put("lecture_id", payload.lectureId());
        body.put("summary_id", payload.summaryId());
        body.put("section_index", payload.sectionIndex());
        body.put("section_summary", payload.sectionSummary());
        body.put("subject", payload.subject());
        body.put("previous_qa", payload.previousQa());
        if (targetTypes != null && !targetTypes.isEmpty()) {
            body.put("question_types", targetTypes);
        }

        log.info("[AI QnA] Stream request: lecture_id={} section_index={} types={}",
                payload.lectureId(), payload.sectionIndex(), targetTypes);

        return webClient.post()
                .uri(baseUrl + "/qa/generate")
                .header(InternalApiKey.HEADER, internalApiKey.value())
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_EVENT_STREAM)
                .bodyValue(body)
                .retrieve()
                .bodyToFlux(SSE_OF_STRING);
    }

    public void requestResourceRecommendation(AiRequestPayloads.ResourceRecommendPayload payload, List<String> targetTypes) {
        Map<String, Object> body = new HashMap<>();

        body.put("lecture_id", String.valueOf(payload.lectureId()));
        body.put("section_id", payload.sectionIndex() + 1);
        body.put("section_index", payload.sectionIndex());
        body.put("section_summary", payload.sectionSummary());

        List<Map<String, Object>> prev = payload.previousSummaries().stream()
                .map(s -> {
                    Map<String, Object> m = new HashMap<>();
                    m.put("section_index", s.sectionIndex());
                    m.put("section_id", s.sectionIndex() + 1);
                    m.put("summary", s.summary());
                    return m;
                })
                .collect(Collectors.toList());
        body.put("previous_summaries", prev);

        body.put("yt_exclude", payload.ytExclude());
        body.put("wiki_exclude", payload.wikiExclude());
        body.put("paper_exclude", payload.paperExclude());
        body.put("google_exclude", payload.googleExclude());

        body.put("callback_url", callback("resources"));

        log.info("[AI Resource] Request: lectureId={} section={} types={}",
                payload.lectureId(), payload.sectionIndex(), targetTypes);

        if (targetTypes != null && !targetTypes.isEmpty()) {
            body.put("resource_types", targetTypes);
        }

        post("/rec/recommend", body);
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

        body.put("phase", phase != null ? phase.toUpperCase() : "FINAL");

        body.put("transcript", transcript);

        body.put("callback_url", callback("summary"));

        log.info("[AI Summary] Request: lectureId={} section={} phase={}", lectureId, sectionIndex, body.get("phase"));

        post("/summary/generate", body);
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

        if (summary.getId() != null) {
            item.put("id", summary.getId().toString());
        }

        item.put("section_id", String.valueOf(summary.getSectionIndex()));
        item.put("metadata", metadata);

        Map<String, Object> body = new HashMap<>();
        body.put("lecture_id", String.valueOf(lectureId));
        body.put("items", List.of(item));

        log.info("[AI RAG] Summary upsert request: lectureId={} summaryId={}", lectureId, summary.getId());

        post("/rag/text-upsert", body);
    }


    public String upsertPdf(Long lectureId, MultipartFile pdfFile) {
        MultipartBodyBuilder builder = new MultipartBodyBuilder();
        builder.part("lecture_id", lectureId.toString());
        builder.part("file", pdfFile.getResource()).filename(pdfFile.getOriginalFilename());

        String url = baseUrl + "/rag/pdf-upsert";

        log.info("[AI RAG] PDF upsert request: lectureId={} file={} size={}B",
                lectureId, pdfFile.getOriginalFilename(), pdfFile.getSize());

        try {
            String responseBody = webClient.post()
                    .uri(url)
                    .header(InternalApiKey.HEADER, internalApiKey.value())
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(BodyInserters.fromMultipartData(builder.build()))
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            // 응답 예: {"collection_id": "lecture_1", "result": {...}}
            String collectionId = objectMapper.readTree(responseBody).get("collection_id").asText();
            log.info("[AI RAG] PDF upsert completed: lectureId={} collectionId={}", lectureId, collectionId);
            return collectionId;

        } catch (Exception e) {
            log.error("[AI Server Call] PDF upsert failed: {}", e.getMessage(), e);
            throw new RuntimeException("RAG Upsert Failed", e);
        }
    }

    // 응답 본문이 필요 없는 요청. 실패하면 AI 서버의 오류 응답을 로그로 남기고 예외를 그대로 던짐
    private void post(String path, Map<String, Object> body) {
        try {
            webClient.post()
                    .uri(baseUrl + path)
                    .header(InternalApiKey.HEADER, internalApiKey.value())
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(body)
                    .retrieve()
                    .toBodilessEntity()
                    .block();
        } catch (WebClientResponseException e) {
            log.error("AI server request failed: path={} status={} body={}",
                    path, e.getStatusCode().value(), e.getResponseBodyAsString());
            throw e;
        } catch (Exception e) {
            log.error("AI server request failed: path={} error={}", path, e.getMessage(), e);
            throw e;
        }
    }
}
