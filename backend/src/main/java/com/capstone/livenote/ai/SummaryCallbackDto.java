package com.capstone.livenote.ai;

import lombok.Builder;

@Builder
public record SummaryCallbackDto(
        Long id,           // 받기만 하고 쓰지 않음
        Long summaryId,    // 받기만 하고 쓰지 않음. 요약은 강의 ID와 섹션 번호로 찾음
        Long lectureId,
        Integer sectionIndex,
        Integer startSec,
        Integer endSec,
        String text,
        String phase,      // "FINAL" / "PARTIAL"
        String status      // "COMPLETED" / "TOO_SHORT" 등
) {}
