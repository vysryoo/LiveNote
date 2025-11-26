package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TranscriptDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Double startSec;
    private Double endSec;
    private String text;
}

