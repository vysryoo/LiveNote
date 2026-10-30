package com.capstone.livenote.global.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.Optional;

@Component
@Slf4j
public class JwtTokenProvider {

    private static final String BEARER_PREFIX = "Bearer ";

    private final SecretKey secretKey;
    private final long validityInMilliseconds;

    public JwtTokenProvider(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration}") long validityInMilliseconds) {
        // Base64 decode 후 SecretKey 생성
        byte[] keyBytes = Decoders.BASE64.decode(secret);
        this.secretKey = Keys.hmacShaKeyFor(keyBytes);
        this.validityInMilliseconds = validityInMilliseconds;
    }

    public String createToken(Long userId) {
        Date now = new Date();
        Date validity = new Date(now.getTime() + validityInMilliseconds);

        return Jwts.builder()
                .subject(String.valueOf(userId))
                .issuedAt(now)
                .expiration(validity)
                .signWith(secretKey)
                .compact();
    }

    /**
     * 접근 토큰의 서명과 만료를 확인하고 사용자 ID를 꺼낸다.
     *
     * @param token 접근 토큰. null 허용
     * @return 사용자 ID. 토큰이 없거나 서명이 틀렸거나 만료됐으면 비어 있음
     */
    public Optional<Long> findUserId(String token) {
        if (token == null) {
            return Optional.empty();
        }
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(secretKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            return Optional.of(Long.parseLong(claims.getSubject()));
        } catch (JwtException | IllegalArgumentException e) {
            log.debug("Invalid JWT token: {}", e.getMessage());
            return Optional.empty();
        }
    }

    /**
     * {@code Authorization} 헤더 값에서 Bearer 토큰을 꺼낸다.
     *
     * @param authorizationHeader 헤더 값. null 허용
     * @return 토큰. 헤더가 없거나 Bearer 형식이 아니면 null
     */
    public static String resolveBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith(BEARER_PREFIX)) {
            return null;
        }
        return authorizationHeader.substring(BEARER_PREFIX.length());
    }
}
