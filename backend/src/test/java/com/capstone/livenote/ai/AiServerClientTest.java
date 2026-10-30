package com.capstone.livenote.ai;

import com.capstone.livenote.ai.AiRequestPayloads.PreviousQaPayload;
import com.capstone.livenote.ai.AiRequestPayloads.PreviousSummaryPayload;
import com.capstone.livenote.ai.AiRequestPayloads.QnaGeneratePayload;
import com.capstone.livenote.ai.AiRequestPayloads.ResourceRecommendPayload;
import com.capstone.livenote.summary.Summary;
import com.capstone.livenote.global.security.InternalApiKey;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.mock.http.client.reactive.MockClientHttpRequest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.reactive.function.client.ClientRequest;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * AI 서버로 보내는 요청의 주소, 헤더, 본문을 고정한다. AI 서버가 이 형식으로 요청을 읽으므로 바뀌면 안 된다.
 */
class AiServerClientTest {

    private static final String AI_SERVER = "http://ai";
    private static final String BACKEND = "http://backend";

    private final ObjectMapper objectMapper = new ObjectMapper();
    private final List<ClientRequest> requests = new ArrayList<>();
    private final List<String> bodies = new ArrayList<>();
    private AiServerClient client;
    private String responseBody = "";
    private MediaType responseType = MediaType.APPLICATION_JSON;

    @BeforeEach
    void setUp() {
        WebClient webClient = WebClient.builder()
                .exchangeFunction(request -> {
                    MockClientHttpRequest written = new MockClientHttpRequest(request.method(), request.url());
                    return request.writeTo(written, ExchangeStrategies.withDefaults())
                            .then(Mono.defer(() -> written.getBodyAsString().defaultIfEmpty("")))
                            .map(body -> {
                                requests.add(request);
                                bodies.add(body);
                                return ClientResponse.create(HttpStatus.OK)
                                        .header(HttpHeaders.CONTENT_TYPE, responseType.toString())
                                        .body(responseBody)
                                        .build();
                            });
                })
                .build();
        client = new AiServerClient(webClient, objectMapper, new InternalApiKey("secret"));
        ReflectionTestUtils.setField(client, "baseUrl", AI_SERVER);
        ReflectionTestUtils.setField(client, "callbackBaseUrl", BACKEND);
    }

    @Test
    void summaryRequest() throws Exception {
        client.requestSummaryGeneration(7L, null, 2, 60, 90, "partial", "전사 내용");

        assertRequest(AI_SERVER + "/summary/generate", """
                {"lecture_id":7,"section_index":2,"start_sec":60,"end_sec":90,"phase":"PARTIAL",
                 "transcript":"전사 내용","callback_url":"http://backend/api/ai/callback?type=summary"}
                """);
    }

    @Test
    void resourceRequest_withTypes() throws Exception {
        client.requestResourceRecommendation(resourcePayload(), List.of("WIKI", "BLOG"));

        assertRequest(AI_SERVER + "/rec/recommend", """
                {"lecture_id":"7","section_id":4,"section_index":3,"section_summary":"요약",
                 "previous_summaries":[{"section_index":2,"section_id":3,"summary":"직전 요약"}],
                 "yt_exclude":["영상"],"wiki_exclude":["위키"],"paper_exclude":["doi/1"],"google_exclude":["http://g"],
                 "callback_url":"http://backend/api/ai/callback?type=resources","resource_types":["WIKI","BLOG"]}
                """);
    }

    @Test
    void resourceRequest_withoutTypes() throws Exception {
        client.requestResourceRecommendation(resourcePayload(), null);

        assertThat(objectMapper.readTree(bodies.get(0)).has("resource_types")).isFalse();
    }

    @Test
    void summaryTextUpsert() throws Exception {
        Summary summary = Summary.builder().id(11L).lectureId(7L).sectionIndex(2).startSec(60).endSec(90).text("요약").build();

        client.upsertSummaryText(7L, summary);

        assertRequest(AI_SERVER + "/rag/text-upsert", """
                {"lecture_id":"7","items":[{"text":"요약","id":"11","section_id":"2",
                 "metadata":{"summaryId":11,"sectionIndex":2,"startSec":60,"endSec":90}}]}
                """);
    }

    @Test
    void qnaStreamRequest() throws Exception {
        responseType = MediaType.TEXT_EVENT_STREAM;
        QnaGeneratePayload payload = QnaGeneratePayload.builder()
                .lectureId(7L).sectionIndex(3).sectionSummary("요약").subject("자료구조")
                .previousQa(List.of(PreviousQaPayload.builder().type("concept").question("질문").answer("답변").build()))
                .build();

        client.streamQnaGeneration(payload, List.of("CONCEPT")).collectList().block();

        assertRequest(AI_SERVER + "/qa/generate", """
                {"lecture_id":7,"summary_id":null,"section_index":3,"section_summary":"요약","subject":"자료구조",
                 "previous_qa":[{"type":"concept","question":"질문","answer":"답변"}],"question_types":["CONCEPT"]}
                """);
        assertThat(requests.get(0).headers().getAccept()).containsExactly(MediaType.TEXT_EVENT_STREAM);
    }

    @Test
    void pdfUpsert() {
        responseBody = "{\"collection_id\":\"lecture_7\"}";
        var pdf = new MockMultipartFile("files", "slides.pdf", "application/pdf", new byte[]{1, 2, 3});

        String collectionId = client.upsertPdf(7L, pdf);

        assertThat(collectionId).isEqualTo("lecture_7");
        assertThat(requests.get(0).url().toString()).isEqualTo(AI_SERVER + "/rag/pdf-upsert");
        assertThat(requests.get(0).headers().getFirst(InternalApiKey.HEADER)).isEqualTo("secret");
        assertThat(bodies.get(0))
                .contains("name=\"lecture_id\"", "name=\"file\"; filename=\"slides.pdf\"")
                .doesNotContain("name=\"base_metadata\"");
    }

    private ResourceRecommendPayload resourcePayload() {
        return ResourceRecommendPayload.builder()
                .lectureId(7L).summaryId(10L).sectionIndex(3).sectionSummary("요약")
                .previousSummaries(List.of(PreviousSummaryPayload.builder().sectionIndex(2).summary("직전 요약").build()))
                .ytExclude(List.of("영상")).wikiExclude(List.of("위키"))
                .paperExclude(List.of("doi/1")).googleExclude(List.of("http://g"))
                .build();
    }

    private void assertRequest(String url, String expectedJson) throws Exception {
        assertThat(requests).hasSize(1);
        ClientRequest request = requests.get(0);
        assertThat(request.url().toString()).isEqualTo(url);
        assertThat(request.headers().getFirst(InternalApiKey.HEADER)).isEqualTo("secret");
        assertThat(objectMapper.readTree(bodies.get(0))).isEqualTo(objectMapper.readTree(expectedJson));
    }
}
