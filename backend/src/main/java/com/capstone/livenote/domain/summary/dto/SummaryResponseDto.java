package com.capstone.livenote.domain.summary.dto;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SummaryResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Integer startSec;
    private Integer endSec;
    private String text;

    private SummaryPhase phase;

    public static SummaryResponseDto from(Summary s) {
        return SummaryResponseDto.builder()
                .id(s.getId())
                .lectureId(s.getLectureId())
                .sectionIndex(s.getSectionIndex())
                .startSec(s.getStartSec())
                .endSec(s.getEndSec())
                .text(s.getText())
                .phase(s.getPhase() != null ? s.getPhase() : SummaryPhase.FINAL)
                .build();
    }
}
