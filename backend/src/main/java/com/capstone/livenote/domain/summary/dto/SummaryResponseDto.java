package com.capstone.livenote.domain.summary.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class SummaryResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Integer startSec;
    private Integer endSec;
    private String text;
}