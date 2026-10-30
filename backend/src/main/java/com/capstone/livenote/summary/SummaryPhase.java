package com.capstone.livenote.summary;

/**
 * 섹션 요약의 단계. 부분 요약은 섹션이 15초, 최종 요약은 30초에 도달하면 요청한다.
 */
public enum SummaryPhase {
    PARTIAL,
    FINAL;

    /**
     * 문자열을 요약 단계로 바꾼다. 대소문자는 구분하지 않는다.
     *
     * @param raw 단계 문자열. null 허용
     * @return {@code PARTIAL}이면 부분 요약, 그 밖의 값이나 null이면 최종 요약
     */
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
