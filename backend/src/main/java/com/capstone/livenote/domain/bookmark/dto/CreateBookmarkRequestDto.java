package com.capstone.livenote.domain.bookmark.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter
@NoArgsConstructor
@AllArgsConstructor
public class CreateBookmarkRequestDto {
    private Long lectureId;
    private Integer sectionIndex;
    private String targetType;    // "resource" | "qna"
    private Long targetId;
}
