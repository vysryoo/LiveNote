package com.capstone.livenote.ai;

import lombok.Builder;

import java.util.List;

/**
 * AI 서버에 보내는 카드 생성 요청 내용. {@link AiServerClient}가 AI 서버 형식(snake_case)의 본문으로 바꿔 보낸다.
 */
public final class AiRequestPayloads {

    private AiRequestPayloads() {}

    @Builder
    public record PreviousSummaryPayload(Integer sectionIndex, String summary) {}

    @Builder
    public record PreviousQaPayload(String type, String question, String answer) {}

    @Builder
    public record ResourceRecommendPayload(
            Long lectureId,
            Long summaryId,
            Integer sectionIndex,
            String sectionSummary,
            List<PreviousSummaryPayload> previousSummaries,
            List<String> ytExclude,
            List<String> wikiExclude,
            List<String> paperExclude,
            List<String> googleExclude
    ) {
        public ResourceRecommendPayload {
            previousSummaries = previousSummaries == null ? List.of() : previousSummaries;
            ytExclude = ytExclude == null ? List.of() : ytExclude;
            wikiExclude = wikiExclude == null ? List.of() : wikiExclude;
            paperExclude = paperExclude == null ? List.of() : paperExclude;
            googleExclude = googleExclude == null ? List.of() : googleExclude;
        }
    }

    @Builder
    public record QnaGeneratePayload(
            Long lectureId,
            Long summaryId,
            Integer sectionIndex,
            String sectionSummary,
            String subject,
            List<PreviousQaPayload> previousQa
    ) {
        public QnaGeneratePayload {
            previousQa = previousQa == null ? List.of() : previousQa;
        }
    }
}
