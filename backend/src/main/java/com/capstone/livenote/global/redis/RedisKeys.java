package com.capstone.livenote.global.redis;

/**
 * 서버 여러 대가 공유하는 Redis 키를 만든다.
 *
 * 키 문자열을 바꾸면 이미 저장된 값(녹음 중인 강의의 섹션 상태, 로그인 상태 등)을 찾지 못하므로 바꾸지 않는다.
 */
public final class RedisKeys {

    private RedisKeys() {}

    /**
     * 갱신 토큰 키. 값은 사용자 ID.
     *
     * @param tokenHash 갱신 토큰의 SHA-256 해시
     * @return Redis 키
     */
    public static String refreshToken(String tokenHash) {
        return "livenote:refresh:" + tokenHash;
    }

    /**
     * 녹음 중인 강의의 섹션 상태 키.
     *
     * @param lectureId 강의 ID
     * @return Redis 키
     */
    public static String sectionState(Long lectureId) {
        return "livenote:lecture:" + lectureId + ":section";
    }

    /**
     * 녹음 중인 강의의 시각 보정값 키.
     *
     * @param lectureId 강의 ID
     * @return Redis 키
     */
    public static String timeOffset(Long lectureId) {
        return "livenote:lecture:" + lectureId + ":offset";
    }

    /**
     * 섹션에서 다음에 생성할 QnA 카드 번호 예약 키.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @return Redis 키
     */
    public static String qnaNextCard(Long lectureId, Integer sectionIndex) {
        return "livenote:lecture:" + lectureId + ":section:" + sectionIndex + ":qna:next-card";
    }

    /**
     * 강의의 전사 저장 잠금 키.
     *
     * @param lectureId 강의 ID
     * @return Redis 키
     */
    public static String transcriptLock(Long lectureId) {
        return "livenote:lock:lecture:" + lectureId + ":transcript";
    }

    /**
     * 섹션의 QnA 카드 저장 잠금 키.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @return Redis 키
     */
    public static String qnaLock(Long lectureId, Integer sectionIndex) {
        return "livenote:lock:lecture:" + lectureId + ":section:" + sectionIndex + ":qna";
    }

    /**
     * 섹션의 자료 카드 저장 잠금 키.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @return Redis 키
     */
    public static String resourceLock(Long lectureId, Integer sectionIndex) {
        return "livenote:lock:lecture:" + lectureId + ":section:" + sectionIndex + ":resource";
    }
}
