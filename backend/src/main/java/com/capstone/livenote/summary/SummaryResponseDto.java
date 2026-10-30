package com.capstone.livenote.summary;

public record SummaryResponseDto(
        Long id,
        Long lectureId,
        Integer sectionIndex,
        Integer startSec,
        Integer endSec,
        String text,
        SummaryPhase phase
) {

    public static SummaryResponseDto from(Summary s) {
        return new SummaryResponseDto(
                s.getId(),
                s.getLectureId(),
                s.getSectionIndex(),
                s.getStartSec(),
                s.getEndSec(),
                s.getText(),
                s.getPhase() != null ? s.getPhase() : SummaryPhase.FINAL
        );
    }
}
