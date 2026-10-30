package com.capstone.livenote.global.redis;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Redis 키 문자열을 고정한다. 바뀌면 이미 저장된 녹음 상태와 갱신 토큰을 찾지 못한다.
 */
class RedisKeysTest {

    @Test
    void keysKeepExistingFormat() {
        assertThat(RedisKeys.refreshToken("abc")).isEqualTo("livenote:refresh:abc");
        assertThat(RedisKeys.sectionState(4L)).isEqualTo("livenote:lecture:4:section");
        assertThat(RedisKeys.timeOffset(4L)).isEqualTo("livenote:lecture:4:offset");
        assertThat(RedisKeys.qnaNextCard(4L, 2)).isEqualTo("livenote:lecture:4:section:2:qna:next-card");
        assertThat(RedisKeys.transcriptLock(4L)).isEqualTo("livenote:lock:lecture:4:transcript");
        assertThat(RedisKeys.qnaLock(4L, 2)).isEqualTo("livenote:lock:lecture:4:section:2:qna");
        assertThat(RedisKeys.resourceLock(4L, 2)).isEqualTo("livenote:lock:lecture:4:section:2:resource");
    }
}
