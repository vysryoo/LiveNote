package com.capstone.livenote.lecture;

public record CreateBookmarkRequestDto(
        Long lectureId,
        Integer sectionIndex,
        Bookmark.TargetType targetType,    // "resource" | "qna"
        Long targetId
) {}
