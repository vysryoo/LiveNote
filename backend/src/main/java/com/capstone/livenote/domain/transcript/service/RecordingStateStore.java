package com.capstone.livenote.domain.transcript.service;

import com.capstone.livenote.global.redis.RedisKeys;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Map;
import java.util.Optional;

/**
 * 녹음 중인 강의의 섹션 상태와 시각 보정값을 Redis에 저장한다.
 *
 * 서버 여러 대가 같은 상태를 보고, 서버가 재시작돼도 상태가 남도록 메모리 대신 Redis를 사용한다.
 * 마지막 저장 후 {@link #TTL}이 지나면 사라지며, 이때는 호출하는 쪽이 DB 기준으로 다시 만든다.
 */
@Component
@RequiredArgsConstructor
public class RecordingStateStore {

    static final Duration TTL = Duration.ofHours(12);

    private final StringRedisTemplate redis;

    /**
     * 섹션 상태.
     *
     * @param index 섹션 번호
     * @param startSec 섹션 첫 전사의 시작 시각(초)
     * @param lastEndSec 섹션 마지막 전사의 끝 시각(초)
     * @param partialRequested 부분 요약을 요청했는지 여부
     * @param finalRequested 최종 요약을 요청했는지 여부. 요청한 뒤 들어오는 전사는 다음 섹션이 됨
     */
    public record SectionState(int index, int startSec, int lastEndSec,
                               boolean partialRequested, boolean finalRequested) {

        public static SectionState start(int index, int startSec, int endSec) {
            return new SectionState(index, startSec, endSec, false, false);
        }

        public int elapsedSec() {
            return lastEndSec - startSec;
        }

        public SectionState withLastEndSec(int value) {
            return new SectionState(index, startSec, value, partialRequested, finalRequested);
        }

        public SectionState withPartialRequested() {
            return new SectionState(index, startSec, lastEndSec, true, finalRequested);
        }

        public SectionState withFinalRequested() {
            return new SectionState(index, startSec, lastEndSec, partialRequested, true);
        }
    }

    /**
     * 클라이언트가 보낸 시각을 강의 전체 기준 시각으로 바꾸기 위한 값.
     *
     * @param base 클라이언트 시각에 더할 값(초)
     * @param lastRawStart 직전에 받은 클라이언트 시작 시각(초). 이보다 작은 값이 오면 녹음이 다시 시작된 것으로 봄
     */
    public record TimeOffset(int base, int lastRawStart) {
    }

    /**
     * 섹션 상태를 조회한다.
     *
     * @param lectureId 강의 ID
     * @return 섹션 상태. 저장된 적이 없거나 만료됐으면 비어 있음
     */
    public Optional<SectionState> findSection(Long lectureId) {
        Map<Object, Object> fields = redis.opsForHash().entries(RedisKeys.sectionState(lectureId));
        if (fields.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new SectionState(
                intOf(fields, "index"),
                intOf(fields, "startSec"),
                intOf(fields, "lastEndSec"),
                boolOf(fields, "partialRequested"),
                boolOf(fields, "finalRequested")));
    }

    /**
     * 섹션 상태를 저장하고 만료 시간을 다시 설정한다.
     *
     * @param lectureId 강의 ID
     * @param state 저장할 섹션 상태
     */
    public void saveSection(Long lectureId, SectionState state) {
        String key = RedisKeys.sectionState(lectureId);
        redis.opsForHash().putAll(key, Map.of(
                "index", String.valueOf(state.index()),
                "startSec", String.valueOf(state.startSec()),
                "lastEndSec", String.valueOf(state.lastEndSec()),
                "partialRequested", String.valueOf(state.partialRequested()),
                "finalRequested", String.valueOf(state.finalRequested())));
        redis.expire(key, TTL);
    }

    /**
     * 시각 보정값을 조회한다.
     *
     * @param lectureId 강의 ID
     * @return 시각 보정값. 저장된 적이 없거나 만료됐으면 비어 있음
     */
    public Optional<TimeOffset> findOffset(Long lectureId) {
        Map<Object, Object> fields = redis.opsForHash().entries(RedisKeys.timeOffset(lectureId));
        if (fields.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(new TimeOffset(intOf(fields, "base"), intOf(fields, "lastRawStart")));
    }

    /**
     * 시각 보정값을 저장하고 만료 시간을 다시 설정한다.
     *
     * @param lectureId 강의 ID
     * @param offset 저장할 시각 보정값
     */
    public void saveOffset(Long lectureId, TimeOffset offset) {
        String key = RedisKeys.timeOffset(lectureId);
        redis.opsForHash().putAll(key, Map.of(
                "base", String.valueOf(offset.base()),
                "lastRawStart", String.valueOf(offset.lastRawStart())));
        redis.expire(key, TTL);
    }

    private static int intOf(Map<Object, Object> fields, String name) {
        return Integer.parseInt((String) fields.get(name));
    }

    private static boolean boolOf(Map<Object, Object> fields, String name) {
        return Boolean.parseBoolean((String) fields.get(name));
    }
}
