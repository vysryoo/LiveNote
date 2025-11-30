package com.capstone.livenote.domain.summary.entity;

public enum SummaryPhase {
    PARTIAL,
    FINAL;

    public static SummaryPhase from(String raw) {
        if (raw == null) {
            return FINAL;
        }
        return switch (raw.trim().toUpperCase()) {
            case "PARTIAL" -> PARTIAL;
            default -> FINAL;
        };
    }
}
