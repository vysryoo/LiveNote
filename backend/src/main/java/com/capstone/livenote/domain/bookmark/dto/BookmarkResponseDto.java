package com.capstone.livenote.domain.bookmark.dto;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
public class BookmarkResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private Bookmark.TargetType targetType; // "resource" / "qna"
    private Long targetId;

    public static BookmarkResponseDto from(Bookmark b) {
        return new BookmarkResponseDto(
                b.getId(),
                b.getLectureId(),
                b.getSectionIndex(),
                b.getTargetType(),
                b.getTargetId()
        );
    }
}
