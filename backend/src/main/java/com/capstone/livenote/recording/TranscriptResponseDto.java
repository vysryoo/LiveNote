package com.capstone.livenote.recording;

public record TranscriptResponseDto(
        Long id,
        Long lectureId,
        Integer sectionIndex,
        Integer startSec,
        Integer endSec,
        String text
) {

    public static TranscriptResponseDto from(Transcript t) {
        return new TranscriptResponseDto(
                t.getId(),
                t.getLectureId(),
                t.getSectionIndex(),
                t.getStartSec(),
                t.getEndSec(),
                t.getText()
        );
    }
}
