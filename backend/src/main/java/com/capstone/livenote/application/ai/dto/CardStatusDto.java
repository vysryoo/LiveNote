package com.capstone.livenote.application.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.List;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CardStatusDto {
    private List<CardItem> qnaCards;
    private List<CardItem> resourceCards;

    @Getter
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class CardItem {
        private String cardId;
        private Integer cardIndex;
        private String type;       // "qna" or "resource"
        private boolean isComplete;
        private Object data;       // QnaResponseDto or ResourceResponseDto
    }
}