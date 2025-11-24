package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CardStatusDto {
    private String cardId;
    private Integer cardIndex;
    private String type;  // "qna" or "resource"
    private Boolean isComplete;
    private Boolean needsStreaming;  // 스트리밍이 필요한지
    private Object data;  // 완료된 경우 데이터 (QnADto 또는 ResourceDto)
}

