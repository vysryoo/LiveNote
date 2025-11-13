package com.capstone.livenote.application.ai.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter @Setter
public class AiCallbackDto {
    private Long lectureId;
    private boolean partial; // true면 중간, false면 최종

    private List<ResourceItem> resources; // 옵션
    private List<QnaItem> qna;            // 옵션
    private List<TranscriptItem> transcripts; // 선택(쓰면 유지)

    @Getter @Setter
    public static class ResourceItem {
        private Integer sectionIndex;
        private String type;     // "paper" | "wiki" | "video" | "blog"
        private String title;
        private String text;
        private String url;
        private String thumbnail;
        private Double score;
    }

    @Getter @Setter
    public static class QnaItem {
        private Integer sectionIndex;
        private String type;     // "concept" | "application" | "advanced" | "comparison"
        private String question;
        private String answer;
    }

    @Getter @Setter
    public static class TranscriptItem { // 필요 시 유지
        private Integer startSec;
        private Integer endSec;
        private String text;
    }
}
