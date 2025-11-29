package com.capstone.livenote.application.ai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

/**
 * AI 서버가 보낸 추천 자료 콜백 DTO
 */
@Getter @Setter
public class ResourceCallbackDto {

    @JsonProperty("lectureId")
    private Long lectureId;

    @JsonProperty("summaryId")
    private Long summaryId;

    @JsonProperty("sectionIndex")
    private Integer sectionIndex;

    @JsonProperty("resources")
    private List<ResourceItem> resources;

    @Getter @Setter
    public static class ResourceItem {
        private String type;        // "blog", "video", "wiki", "paper"
        private String title;
        private String url;
        private String description;
        private Double score;
        private String reason;
        private Map<String, Object> detail;
    }
}
