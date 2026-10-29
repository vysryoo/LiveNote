package com.capstone.livenote.global.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.Base64;
import java.util.HexFormat;
import java.util.Optional;

/**
 * 접근 토큰을 다시 발급받기 위한 갱신 토큰을 발급, 교체, 폐기한다.
 *
 * 갱신 토큰은 임의의 문자열이며 Redis에 해시만 저장한다. 한 번 쓰면 폐기하고 새 토큰을 발급한다(교체).
 */
@Service
public class RefreshTokenService {

    private static final SecureRandom RANDOM = new SecureRandom();
    private static final int TOKEN_BYTES = 32;

    private final StringRedisTemplate redis;
    private final Duration validity;

    public RefreshTokenService(StringRedisTemplate redis,
                               @Value("${app.jwt.refresh-expiration-days}") long validityDays) {
        this.redis = redis;
        this.validity = Duration.ofDays(validityDays);
    }

    /** 교체 결과. 사용자 ID와 새로 발급한 갱신 토큰. */
    public record Rotation(Long userId, String refreshToken) {
    }

    /**
     * 사용자에게 새 갱신 토큰을 발급한다.
     *
     * @param userId 사용자 ID
     * @return 발급한 갱신 토큰. 서버에는 해시만 남으므로 이 값을 잃으면 다시 쓸 수 없음
     */
    public String issue(Long userId) {
        byte[] bytes = new byte[TOKEN_BYTES];
        RANDOM.nextBytes(bytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        redis.opsForValue().set(key(token), String.valueOf(userId), validity);
        return token;
    }

    /**
     * 갱신 토큰을 폐기하고 같은 사용자에게 새 갱신 토큰을 발급한다.
     *
     * 조회와 삭제를 한 번에 수행하므로, 같은 토큰으로 동시에 요청하면 하나만 성공한다.
     *
     * @param token 브라우저가 보낸 갱신 토큰. null 허용
     * @return 교체 결과. 토큰이 없거나 만료·폐기됐으면 비어 있음
     */
    public Optional<Rotation> rotate(String token) {
        if (token == null || token.isBlank()) {
            return Optional.empty();
        }
        String userId = redis.opsForValue().getAndDelete(key(token));
        if (userId == null) {
            return Optional.empty();
        }
        Long id = Long.parseLong(userId);
        return Optional.of(new Rotation(id, issue(id)));
    }

    /**
     * 갱신 토큰을 폐기한다. 이미 없는 토큰이면 아무것도 하지 않는다.
     *
     * @param token 폐기할 갱신 토큰. null 허용
     */
    public void revoke(String token) {
        if (token == null || token.isBlank()) {
            return;
        }
        redis.delete(key(token));
    }

    /**
     * 쿠키 만료 시간으로 쓸 갱신 토큰 유효 기간을 반환한다.
     *
     * @return 유효 기간
     */
    public Duration validity() {
        return validity;
    }

    private static String key(String token) {
        return "livenote:refresh:" + sha256(token);
    }

    private static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }
}
