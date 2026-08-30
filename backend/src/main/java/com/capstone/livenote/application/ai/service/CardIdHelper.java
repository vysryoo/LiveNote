package com.capstone.livenote.application.ai.service;

public final class CardIdHelper {
    public static final int CARD_INDEX_OFFSET = 2;

    private CardIdHelper() {}

    public static String buildCardId(String prefix, Long lectureId, Integer sectionIndex, int cardIndex) {
        return prefix + "_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
    }

    public static int extractCardIndex(String cardId, int fallback) {
        if (cardId == null || cardId.isBlank()) {
            return fallback;
        }
        String[] parts = cardId.split("_");
        if (parts.length < 4) {
            return fallback;
        }
        try {
            return Integer.parseInt(parts[3]);
        } catch (NumberFormatException e) {
            return fallback;
        }
    }
}
