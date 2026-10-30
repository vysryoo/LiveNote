package com.capstone.livenote.lecture;

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
    private Bookmark.TargetType targetType;;    // "resource" | "qna"
    private Long targetId;
}
