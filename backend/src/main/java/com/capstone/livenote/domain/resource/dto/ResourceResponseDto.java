package com.capstone.livenote.domain.resource.dto;

import com.capstone.livenote.domain.resource.entity.Resource;
import com.fasterxml.jackson.databind.JsonNode;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
public class ResourceResponseDto {
    private Long id;
    private Long lectureId;
    private Long summaryId;
    private Integer sectionIndex;
    private String type;
    private String title;
    private String url;
    private String thumbnail;
    private Double score;
    private String text;
    private String reason;
    private JsonNode detail;

    public static ResourceResponseDto from(Resource r) {
        return new ResourceResponseDto(
                r.getId(),
                r.getLectureId(),
                r.getSummaryId(),
                r.getSectionIndex(),
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
