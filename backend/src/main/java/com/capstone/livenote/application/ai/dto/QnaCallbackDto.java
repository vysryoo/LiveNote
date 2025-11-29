package com.capstone.livenote.application.ai.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;
import java.util.List;

/**
 * AI 서버가 생성한 QnA 콜백 DTO
 */
@Getter @Setter
@JsonIgnoreProperties(ignoreUnknown = true)
public class QnaCallbackDto {

    private Long lectureId;

    private Long summaryId;

    private Integer sectionIndex;

    @JsonProperty("qnaList")
    private List<QnaItem> qnaList;


    @Getter @Setter
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class QnaItem {
        private String type;     // "concept" | "application" | "advanced" | "comparison"
        private String question;
        private String answer;
    }
}