package com.capstone.livenote.application.ai.client;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

//@Component
@RequiredArgsConstructor
public class WebAiClient implements AiClient {

    private final WebClient webClient;

    @Value("${ai.base-url}")
    private String baseUrl;

    @Override
    public void sendChunk(Long lectureId, int chunkSeq, int startSec, int endSec, String fileUri) {
        var body = Map.of(
                "lectureId", lectureId,
                "chunkSeq", chunkSeq,
                "startSec", startSec,
                "endSec", endSec,
                "fileUri", fileUri
        );
        webClient.post()
                .uri(baseUrl + "/ingest/chunk")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    @Override
    public void notifyComplete(Long lectureId) {
        webClient.post()
                .uri(baseUrl + "/ingest/complete")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(Map.of("lectureId", lectureId))
                .retrieve()
                .toBodilessEntity()
                .block();
    }

    @Override
    public void requestResourcesAndQna(Long lectureId, Long summaryId, Integer sectionIndex) {
        var body = Map.of(
                "lectureId", lectureId,
                "summaryId", summaryId,
                "sectionIndex", sectionIndex
        );
        webClient.post()
                .uri(baseUrl + "/generate/resources-qna")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(body)
                .retrieve()
                .toBodilessEntity()
                .block();
    }
}
