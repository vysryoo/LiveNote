package com.capstone.livenote.domain.resource.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
public class ResourceRequestDto {

    private Long lectureId;
    private Long summaryId;
    private Long userId;
    private Integer sectionIndex;

    private String type;       // "paper" | "wiki" | "video" | "blog"
    private String title;
    private String text;
    private String url;
    private String thumbnail;

    private Double score;
}

