package com.capstone.livenote.application.ai.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;

/**
 * AI 서버가 보낸 추천 자료 콜백 DTO
 */
@Getter @Setter
public class ResourceCallbackDto {

    private Long lectureId;
    private Long summaryId;
    private Integer sectionIndex;

    private List<ResourceItem> resources;

    @Getter @Setter
    public static class ResourceItem {
        private String type;        // "blog", "video", "wiki" 등
        private String title;
        private String url;
        private String description;
        private Double score;       // 유사도 / 랭킹 점수
        private String reason;
        private Map<String, Object> detail;
    }
}
