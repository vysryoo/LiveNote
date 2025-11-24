package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BookmarkDto {
    private Long id;
    private Long userId;
    private Long lectureId;
    private Integer sectionIndex;
    private String targetType;
    private Long targetId;
}

