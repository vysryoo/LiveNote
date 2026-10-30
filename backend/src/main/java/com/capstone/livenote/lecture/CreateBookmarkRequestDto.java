package com.capstone.livenote.lecture;

public record CreateBookmarkRequestDto(
        Long lectureId,
        Integer sectionIndex,
        Bookmark.TargetType targetType,    // "RESOURCE" | "QNA". 소문자는 받지 않음
        Long targetId
) {}
