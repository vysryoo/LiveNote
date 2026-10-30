package com.capstone.livenote.card;

import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CardIdsTest {

    @Test
    void build_followsFrontendFormat() {
        assertThat(CardIds.build("qna", 7L, 3, 2)).isEqualTo("qna_7_3_2");
    }

    @Test
    void nextIndex_startsAtFirstIndexAndFollowsLargestNumber() {
        assertThat(CardIds.nextIndex(List.of())).isEqualTo(CardIds.FIRST_INDEX);
        assertThat(CardIds.nextIndex(List.of("resource_7_3_2", "resource_7_3_5", "resource_7_3_3"))).isEqualTo(6);
        // 형식이 맞지 않는 ID는 번호가 없는 것으로 봄
        assertThat(CardIds.nextIndex(Arrays.asList("broken", null, "qna_7_3_x"))).isEqualTo(CardIds.FIRST_INDEX);
    }

    @Test
    void signature_ignoresSurroundingSpacesAndNulls() {
        assertThat(CardIds.signature(" 제목 ", "http://a ")).isEqualTo(CardIds.signature("제목", "http://a"));
        assertThat(CardIds.signature(null, null)).isEqualTo("|");
    }

    @Test
    void qnaType_acceptsEnglishAndKoreanNames() {
        assertThat(Qna.Type.from("응용")).isEqualTo(Qna.Type.APPLICATION);
        assertThat(Qna.Type.from(" comparison ")).isEqualTo(Qna.Type.COMPARISON);
        assertThat(Qna.Type.from("unknown")).isEqualTo(Qna.Type.CONCEPT);
        assertThat(Qna.Type.from(null)).isEqualTo(Qna.Type.CONCEPT);
    }
}
