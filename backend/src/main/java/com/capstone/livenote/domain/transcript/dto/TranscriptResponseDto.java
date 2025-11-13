package com.capstone.livenote.domain.transcript.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class TranscriptResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Integer startSec;
    private Integer endSec;
    private String text;
}