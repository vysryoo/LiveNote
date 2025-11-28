package com.capstone.livenote.application.ai.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SummaryCallbackDto {
    private Long id;           // AI 서버 내부 ID (안 써도 됨)
    private Long summaryId;    // 우리 DB summary PK 와 연결 용도 (없을 수도)
    private Long lectureId;
    private Integer sectionIndex;
    private Integer startSec;
    private Integer endSec;
    private String text;
    private String phase;      // "FINAL" / "PARTIAL"
}
