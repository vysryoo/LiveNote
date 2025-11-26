package com.livenote.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class BookmarkRequest {
    @NotNull(message = "강의 ID는 필수입니다")
    private Long lectureId;
    
    @NotNull(message = "섹션 인덱스는 필수입니다")
    private Integer sectionIndex;
    
    @NotNull(message = "대상 타입은 필수입니다")
    private String targetType;
    
    @NotNull(message = "대상 ID는 필수입니다")
    private Long targetId;
}

