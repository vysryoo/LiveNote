package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ResourceDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private String type;
    private String title;
    private String text;
    private String url;
    private String thumbnail;
    private Double score;
}

