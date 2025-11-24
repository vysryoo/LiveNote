package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class QnADto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private String type;
    private String question;
    private String answer;
}

