package com.capstone.livenote.global.security;

import org.junit.jupiter.api.Test;

import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;

class JwtTokenProviderTest {

    private static final String SECRET = Base64.getEncoder().encodeToString(new byte[32]);

    private final JwtTokenProvider provider = new JwtTokenProvider(SECRET, 60_000);

    @Test
    void findUserId_returnsSubjectOfValidToken() {
        assertThat(provider.findUserId(provider.createToken(7L))).contains(7L);
    }

    @Test
    void findUserId_rejectsTamperedExpiredOrMissingToken() {
        String token = provider.createToken(7L);
        String expired = new JwtTokenProvider(SECRET, -1_000).createToken(7L);
        byte[] otherSecret = new byte[32];
        otherSecret[0] = 1;
        String otherKey = new JwtTokenProvider(Base64.getEncoder().encodeToString(otherSecret), 60_000).createToken(7L);

        assertThat(provider.findUserId(token + "x")).isEmpty();
        assertThat(provider.findUserId(expired)).isEmpty();
        assertThat(provider.findUserId(otherKey)).isEmpty();
        assertThat(provider.findUserId(null)).isEmpty();
        assertThat(provider.findUserId("not-a-jwt")).isEmpty();
    }

    @Test
    void resolveBearerToken_acceptsOnlyBearerHeader() {
        assertThat(JwtTokenProvider.resolveBearerToken("Bearer abc")).isEqualTo("abc");
        assertThat(JwtTokenProvider.resolveBearerToken("Basic abc")).isNull();
        assertThat(JwtTokenProvider.resolveBearerToken(null)).isNull();
    }
}
