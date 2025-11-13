package com.capstone.livenote.domain.bookmark.dto;

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
    private String targetType; // 응답도 소문자로 통일
    private Long targetId;

    public BookmarkResponseDto(Long id, Long userId, Long lectureId, Integer sectionIndex, String lowerCase, Long targetId) {
    }
}
