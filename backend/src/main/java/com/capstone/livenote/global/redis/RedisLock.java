package com.capstone.livenote.global.redis;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.List;
import java.util.UUID;
import java.util.function.Supplier;

/**
 * 서버 여러 대에 걸쳐 같은 키의 작업을 한 번에 하나씩 실행하게 하는 Redis 잠금.
 *
 * 잠금은 최대 {@link #LEASE} 동안 유지된다. 작업이 그보다 오래 걸리면 잠금이 먼저 풀릴 수 있다.
 */
@Component
@RequiredArgsConstructor
public class RedisLock {

    static final Duration LEASE = Duration.ofSeconds(30);
    static final Duration WAIT = Duration.ofSeconds(10);
    private static final long RETRY_INTERVAL_MS = 50;

    // 다른 요청이 잡은 잠금을 지우지 않도록 본인이 넣은 값일 때만 삭제
    private static final RedisScript<Long> RELEASE = new DefaultRedisScript<>(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
            Long.class);

    private final StringRedisTemplate redis;

    /**
     * 잠금을 잡은 상태에서 작업을 실행하고 결과를 반환한다.
     *
     * @param key 잠금 키
     * @param action 실행할 작업
     * @return 작업 결과
     * @throws IllegalStateException {@link #WAIT} 안에 잠금을 얻지 못했거나 기다리는 중 인터럽트된 경우. 작업은 실행되지 않음
     */
    public <T> T call(String key, Supplier<T> action) {
        String token = UUID.randomUUID().toString();
        acquire(key, token);
        try {
            return action.get();
        } finally {
            redis.execute(RELEASE, List.of(key), token);
        }
    }

    /**
     * 잠금을 잡은 상태에서 작업을 실행한다.
     *
     * @param key 잠금 키
     * @param action 실행할 작업
     * @throws IllegalStateException {@link #WAIT} 안에 잠금을 얻지 못했거나 기다리는 중 인터럽트된 경우. 작업은 실행되지 않음
     */
    public void run(String key, Runnable action) {
        call(key, () -> {
            action.run();
            return null;
        });
    }

    private void acquire(String key, String token) {
        long deadline = System.nanoTime() + WAIT.toNanos();
        while (!Boolean.TRUE.equals(redis.opsForValue().setIfAbsent(key, token, LEASE))) {
            if (System.nanoTime() > deadline) {
                throw new IllegalStateException("lock timeout: " + key);
            }
            try {
                Thread.sleep(RETRY_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("interrupted while waiting for lock: " + key, e);
            }
        }
    }
}
