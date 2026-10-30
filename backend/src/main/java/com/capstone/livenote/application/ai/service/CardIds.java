package com.capstone.livenote.application.ai.service;

import java.util.Collection;

/**
 * 카드 ID를 만들고, 섹션에 새로 추가할 카드의 번호를 정한다.
 *
 * 카드 ID 형식은 {@code {접두사}_{강의 ID}_{섹션}_{카드 번호}}다. 프론트엔드가 이 형식에서 섹션과 카드 번호를 꺼내 쓴다.
 */
public final class CardIds {

    /** 섹션의 첫 카드 번호 */
    public static final int FIRST_INDEX = 2;

    private CardIds() {}

    /**
     * 카드 ID를 만든다.
     *
     * @param prefix 카드 종류 접두사. {@code qna} 또는 {@code resource}
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param cardIndex 카드 번호
     * @return 카드 ID
     */
    public static String build(String prefix, Long lectureId, Integer sectionIndex, int cardIndex) {
        return prefix + "_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
    }

    /**
     * 섹션에 이미 있는 카드들 다음에 쓸 카드 번호를 정한다.
     *
     * @param cardIds 섹션에 저장된 카드의 ID. 형식이 맞지 않는 ID는 번호가 없는 것으로 봄
     * @return 가장 큰 카드 번호 + 1. 카드가 없으면 {@link #FIRST_INDEX}
     */
    public static int nextIndex(Collection<String> cardIds) {
        return cardIds.stream()
                .mapToInt(CardIds::parseIndex)
                .max()
                .orElse(FIRST_INDEX - 1) + 1;
    }

    /**
     * 같은 내용의 카드인지 비교할 키를 만든다. 앞뒤 공백은 무시한다.
     *
     * @param first 제목 또는 질문. null 허용
     * @param second URL 또는 답변. null 허용
     * @return 비교용 키
     */
    public static String signature(String first, String second) {
        return (first == null ? "" : first.trim()) + "|" + (second == null ? "" : second.trim());
    }

    private static int parseIndex(String cardId) {
        if (cardId == null || cardId.isBlank()) {
            return FIRST_INDEX - 1;
        }
        String[] parts = cardId.split("_");
        if (parts.length < 4) {
            return FIRST_INDEX - 1;
        }
        try {
            return Integer.parseInt(parts[3]);
        } catch (NumberFormatException e) {
            return FIRST_INDEX - 1;
        }
    }
}
