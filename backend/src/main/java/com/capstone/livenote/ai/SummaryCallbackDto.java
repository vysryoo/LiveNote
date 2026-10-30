package com.capstone.livenote.ai;

import lombok.Builder;

@Builder
public record SummaryCallbackDto(
        Long id,           // AI 서버 내부 ID (안 써도 됨)
        Long summaryId,    // 우리 DB summary PK 와 연결 용도 (없을 수도)
        Long lectureId,
        Integer sectionIndex,
        Integer startSec,
        Integer endSec,
        String text,
        String phase,      // "FINAL" / "PARTIAL"
        String status      // "COMPLETED" / "TOO_SHORT" 등
) {}
