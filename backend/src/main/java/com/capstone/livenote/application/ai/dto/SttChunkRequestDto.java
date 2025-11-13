package com.capstone.livenote.application.ai.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.ToString;

//STT 서버가 보내는 한 덩어리(구간) 전사 데이터
@Getter
@NoArgsConstructor
@AllArgsConstructor
@ToString
public class SttChunkRequestDto {
    private Integer startSec; // 구간 시작 시각(초)
    private Integer endSec;   // 구간 끝 시각(초)
    private String text;      // 해당 구간 전사 텍스트
}
