package com.capstone.livenote.lecture;

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

    public static BookmarkResponseDto from(Bookmark b) {

        String type = (b.getTargetType() != null)
                ? b.getTargetType().name().toLowerCase()
                : null;

        return BookmarkResponseDto.builder()
                .id(b.getId())
                .lectureId(b.getLectureId())
                .sectionIndex(b.getSectionIndex())
                .targetType(type)
                .targetId(b.getTargetId())
                .build();
    }
}
