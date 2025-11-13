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
    private String type;
    private String question;
    private String answer;

    public QnaResponseDto(Long id, Long id1, Qna.Type type, String question, String answer) {
    }
}
