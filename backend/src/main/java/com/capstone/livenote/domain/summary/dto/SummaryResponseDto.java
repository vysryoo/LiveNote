package com.capstone.livenote.domain.summary.dto;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.*;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SummaryResponseDto {
    public enum Phase { PARTIAL, FINAL }
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Integer startSec;
    private Integer endSec;
    private String text;

    private Phase phase;

    public static SummaryResponseDto from(Summary s) {
        return SummaryResponseDto.builder()
                .id(s.getId())
                .lectureId(s.getLectureId())
                .sectionIndex(s.getSectionIndex())
                .startSec(s.getStartSec())
                .endSec(s.getEndSec())
                .text(s.getText())
                .phase(toDtoPhase(s.getPhase()))
                .build();
    }

    private static Phase toDtoPhase(SummaryPhase phase) {
        if (phase == null) {
            return Phase.FINAL;
        }
        return switch (phase) {
            case PARTIAL -> Phase.PARTIAL;
            case FINAL -> Phase.FINAL;
        };
    }
}
