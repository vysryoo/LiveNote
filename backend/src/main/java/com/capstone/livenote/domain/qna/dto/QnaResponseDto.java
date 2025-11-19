package com.capstone.livenote.domain.qna.dto;

import com.capstone.livenote.domain.qna.entity.Qna;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class QnaResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Qna.Type type;
    private String question;
    private String answer;

    public static QnaResponseDto from(Qna q) {
        return new QnaResponseDto(
                q.getId(),
                q.getLectureId(),
                q.getSectionIndex(),
                q.getType(),
                q.getQuestion(),
                q.getAnswer()
        );
    }
}
