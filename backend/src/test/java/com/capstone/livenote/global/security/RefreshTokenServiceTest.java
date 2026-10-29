package com.capstone.livenote.global.security;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class RefreshTokenServiceTest {

    @Mock StringRedisTemplate redis;
    @Mock ValueOperations<String, String> values;

    private final Map<String, String> store = new HashMap<>();
    private RefreshTokenService service;

    @BeforeEach
    void setUp() {
        service = new RefreshTokenService(redis, 14);
        when(redis.opsForValue()).thenReturn(values);
        doAnswer(inv -> {
            store.put(inv.getArgument(0), inv.getArgument(1));
            return null;
        }).when(values).set(anyString(), anyString(), any(Duration.class));
        when(values.getAndDelete(anyString())).thenAnswer(inv -> store.remove(inv.<String>getArgument(0)));
        when(redis.delete(anyString())).thenAnswer(inv -> store.remove(inv.<String>getArgument(0)) != null);
    }

    @Test
    void issue_storesOnlyHashWithValidity() {
        String token = service.issue(7L);

        assertThat(token).hasSizeGreaterThanOrEqualTo(43);
        assertThat(store).hasSize(1);
        String key = store.keySet().iterator().next();
        assertThat(key).startsWith("livenote:refresh:").doesNotContain(token);
        assertThat(store.get(key)).isEqualTo("7");
        verify(values).set(eq(key), eq("7"), eq(Duration.ofDays(14)));
    }

    @Test
    void rotate_returnsUserAndReplacesToken() {
        String first = service.issue(7L);

        var rotation = service.rotate(first).orElseThrow();

        assertThat(rotation.userId()).isEqualTo(7L);
        assertThat(rotation.refreshToken()).isNotEqualTo(first);
        assertThat(service.rotate(first)).isEmpty();
        assertThat(service.rotate(rotation.refreshToken())).isPresent();
    }

    @Test
    void rotate_rejectsMissingOrUnknownToken() {
        assertThat(service.rotate(null)).isEmpty();
        assertThat(service.rotate(" ")).isEmpty();
        assertThat(service.rotate("unknown")).isEmpty();
    }

    @Test
    void revoke_makesTokenUnusable() {
        String token = service.issue(7L);

        service.revoke(token);

        assertThat(service.rotate(token)).isEmpty();
    }
}
