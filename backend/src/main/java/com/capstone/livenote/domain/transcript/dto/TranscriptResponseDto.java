package com.capstone.livenote.domain.transcript.dto;

import com.capstone.livenote.domain.transcript.entity.Transcript;
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