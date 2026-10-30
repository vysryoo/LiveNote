package com.capstone.livenote.lecture;

public record BookmarkResponseDto(
        Long id,
        Long lectureId,
        Integer sectionIndex,
        String targetType, // "resource" / "qna"
        Long targetId
) {

    public static BookmarkResponseDto from(Bookmark b) {
        String type = (b.getTargetType() != null)
                ? b.getTargetType().name().toLowerCase()
                : null;
        return new BookmarkResponseDto(b.getId(), b.getLectureId(), b.getSectionIndex(), type, b.getTargetId());
    }
}
