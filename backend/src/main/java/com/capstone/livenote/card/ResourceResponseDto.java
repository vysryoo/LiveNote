package com.capstone.livenote.card;

import com.fasterxml.jackson.databind.JsonNode;

public record ResourceResponseDto(
        Long id,
        Long lectureId,
        Long summaryId,
        Integer sectionIndex,
        String cardId,
        String type,
        String title,
        String url,
        String thumbnail,
        Double score,
        String text,
        String reason,
        JsonNode detail
) {

    public static ResourceResponseDto from(Resource r) {
        return new ResourceResponseDto(
                r.getId(),
                r.getLectureId(),
                r.getSummaryId(),
                r.getSectionIndex(),
                r.getCardId(),
                r.getType().name().toLowerCase(),
                r.getTitle(),
                r.getUrl(),
                r.getThumbnail(),
                r.getScore(),
                r.getText(),
                r.getReason(),
                r.getDetail()
        );
    }
}
