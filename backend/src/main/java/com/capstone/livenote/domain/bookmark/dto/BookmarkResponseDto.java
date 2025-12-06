package com.capstone.livenote.domain.bookmark.dto;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import lombok.*;

@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
@Builder
public class BookmarkResponseDto {
    private Long id;
    private Long lectureId;
    private Integer sectionIndex;
    private String targetType; // "resource" / "qna"
    private Long targetId;
    private Object content;

    public static BookmarkResponseDto from(Bookmark b) {

        return BookmarkResponseDto.builder()
                .id(b.getId())
                .lectureId(b.getLectureId())
                .sectionIndex(b.getSectionIndex())
                .targetType(b.getTargetType().name())
                .targetId(b.getTargetId())
                .build();
    }

    public static BookmarkResponseDto from(Bookmark b, Object content) {

        String type = (b.getTargetType() != null)
                ? b.getTargetType().name()
                : null;


        return BookmarkResponseDto.builder()
                .id(b.getId())
                .lectureId(b.getLectureId())
                .sectionIndex(b.getSectionIndex())
                .targetType(type)
                .targetId(b.getTargetId())
                .content(content)
                .build();
    }
}
