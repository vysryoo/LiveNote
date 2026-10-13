package com.capstone.livenote.global.security;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class InternalApiKeyTest {

    @Test
    void matches_sameKey() {
        assertThat(new InternalApiKey("secret-key").matches("secret-key")).isTrue();
    }

    @Test
    void rejects_differentOrMissingKey() {
        InternalApiKey key = new InternalApiKey("secret-key");
        assertThat(key.matches("other-key")).isFalse();
        assertThat(key.matches(null)).isFalse();
    }

    @Test
    void rejects_everythingWhenServerKeyIsBlank() {
        assertThat(new InternalApiKey("").matches("")).isFalse();
        assertThat(new InternalApiKey(null).matches(null)).isFalse();
    }
}
