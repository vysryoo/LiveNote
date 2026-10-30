package com.capstone.livenote.ai;

import lombok.Builder;

import java.util.List;
import java.util.Map;

/**
 * AI 서버가 보낸 추천 자료 콜백 DTO
 */
@Builder
public record ResourceCallbackDto(
        Long lectureId,
        Long summaryId,
        Integer sectionIndex,
        List<ResourceItem> resources
) {

    @Builder
    public record ResourceItem(
            String type,        // "blog", "video", "wiki", "paper"
            String title,
            String url,
            String description,
            Double score,
            String reason,
            Map<String, Object> detail
    ) {}
}
