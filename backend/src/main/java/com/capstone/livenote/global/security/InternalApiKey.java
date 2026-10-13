package com.capstone.livenote.global.security;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * 백엔드와 AI 서버가 공유하는 내부 키.
 *
 * 백엔드가 AI 서버를 호출할 때와 AI 서버가 콜백을 보낼 때 같은 헤더로 서로를 확인한다.
 */
@Component
public class InternalApiKey {

    public static final String HEADER = "X-Internal-Api-Key";

    private final String key;

    public InternalApiKey(@Value("${app.internal-api-key}") String key) {
        this.key = key;
    }

    /**
     * AI 서버로 보내는 요청에 붙일 헤더 값을 반환한다.
     *
     * @return 공유 키
     */
    public String value() {
        return key;
    }

    /**
     * 요청 헤더의 키가 공유 키와 같은지 확인한다.
     *
     * @param provided 요청 헤더 값. 없으면 null
     * @return 일치하면 true. 서버에 키가 설정되지 않았으면 항상 false
     */
    public boolean matches(String provided) {
        if (key == null || key.isBlank() || provided == null) {
            return false;
        }
        // 비교 시간으로 키를 추측하지 못하도록 고정 시간 비교 사용
        return MessageDigest.isEqual(
                key.getBytes(StandardCharsets.UTF_8),
                provided.getBytes(StandardCharsets.UTF_8)
        );
    }
}
