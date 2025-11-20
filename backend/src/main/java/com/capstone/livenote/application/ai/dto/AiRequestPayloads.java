package com.capstone.livenote.application.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

public class AiRequestPayloads {

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PreviousSummaryPayload {
        private Integer sectionIndex;
        private String summary;
    }

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PreviousQaPayload {
        private String type;
        private String question;
        private String answer;
    }

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ResourceRecommendPayload {
        private Long lectureId;
        private Long summaryId;
        private Integer sectionIndex;
        private String sectionSummary;
        @Builder.Default
        private List<PreviousSummaryPayload> previousSummaries = new ArrayList<>();
        @Builder.Default
        private List<String> ytExclude = new ArrayList<>();
        @Builder.Default
        private List<String> wikiExclude = new ArrayList<>();
        @Builder.Default
        private List<String> paperExclude = new ArrayList<>();
        @Builder.Default
        private List<String> googleExclude = new ArrayList<>();
    }

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class QnaGeneratePayload {
        private Long lectureId;
        private Long summaryId;
        private Integer sectionIndex;
        private String sectionSummary;
        private String subject;
        @Builder.Default
        private List<PreviousQaPayload> previousQa = new ArrayList<>();
    }
}
