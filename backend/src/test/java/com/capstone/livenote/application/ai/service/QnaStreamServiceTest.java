package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.AiServerClient;
import com.capstone.livenote.application.ai.dto.AiRequestPayloads.QnaGeneratePayload;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.global.redis.RedisLock;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.transaction.support.TransactionCallback;
import org.springframework.transaction.support.TransactionTemplate;
import reactor.core.publisher.Flux;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class QnaStreamServiceTest {

    private static final long LECTURE = 1L;
    private static final int SECTION = 5;
    private static final String RESERVATION_KEY = "livenote:lecture:1:section:5:qna:next-card";

    @Mock AiServerClient aiServerClient;
    @Mock QnaRepository qnaRepository;
    @Mock StreamGateway streamGateway;
    @Mock RedisLock redisLock;
    @Mock TransactionTemplate transactionTemplate;
    @Mock StringRedisTemplate redis;
    @Mock ValueOperations<String, String> valueOperations;

    private QnaStreamService service;
    private final List<Qna> stored = new ArrayList<>();
    private final Map<String, String> redisValues = new HashMap<>();

    @BeforeEach
    void setUp() {
        service = new QnaStreamService(aiServerClient, qnaRepository, streamGateway, redisLock,
                transactionTemplate, redis, new ObjectMapper());

        when(redisLock.call(anyString(), any())).thenAnswer(inv -> inv.<Supplier<?>>getArgument(1).get());
        when(transactionTemplate.execute(any())).thenAnswer(inv -> inv.<TransactionCallback<?>>getArgument(0).doInTransaction(null));

        when(redis.opsForValue()).thenReturn(valueOperations);
        when(valueOperations.get(anyString())).thenAnswer(inv -> redisValues.get(inv.<String>getArgument(0)));
        doAnswer(inv -> {
            redisValues.put(inv.getArgument(0), inv.getArgument(1));
            return null;
        }).when(valueOperations).set(anyString(), anyString(), any());

        when(qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(LECTURE, SECTION))
                .thenAnswer(inv -> List.copyOf(stored));
        when(qnaRepository.save(any(Qna.class))).thenAnswer(inv -> {
            Qna qna = inv.getArgument(0);
            qna.setId(100L + stored.size());
            stored.add(qna);
            return qna;
        });
    }

    private QnaGeneratePayload payload() {
        return QnaGeneratePayload.builder().lectureId(LECTURE).summaryId(10L).sectionIndex(SECTION).build();
    }

    private static ServerSentEvent<String> sse(String event, String data) {
        return ServerSentEvent.<String>builder().event(event).data(data).build();
    }

    @SafeVarargs
    private void relay(ServerSentEvent<String>... events) {
        service.relay(payload(), Flux.just(events)).block();
    }

    @Test
    void relaysQuestionAndAnswerTokensThenSavesCard() {
        relay(
                sse("start", "{\"item\":0,\"type\":\"APPLICATION\"}"),
                sse("question", "{\"item\":0,\"text\":\"재시도 패턴?\"}"),
                sse("answer", "{\"item\":0,\"text\":\"exponential \"}"),
                sse("answer", "{\"item\":0,\"text\":\"backoff\"}"),
                sse("done", "{\"item\":0,\"type\":\"APPLICATION\",\"question\":\"재시도 패턴?\",\"answer\":\"exponential backoff\"}"));

        String cardId = "qna_1_5_2";
        InOrder order = inOrder(streamGateway);
        order.verify(streamGateway).sendStreamToken(LECTURE, "qna_stream", cardId, "", "재시도 패턴?");
        order.verify(streamGateway).sendStreamToken(LECTURE, "qna_stream", cardId, "exponential ", "재시도 패턴?");
        order.verify(streamGateway).sendStreamToken(LECTURE, "qna_stream", cardId, "backoff", "재시도 패턴?");
        order.verify(streamGateway).sendStreamComplete(eq(LECTURE), eq("qna_stream"), eq(cardId), any(QnaResponseDto.class));
        order.verify(streamGateway).sendQna(eq(LECTURE), eq(SECTION), any());

        assertThat(stored).hasSize(1);
        Qna saved = stored.get(0);
        assertThat(saved.getCardId()).isEqualTo(cardId);
        assertThat(saved.getType()).isEqualTo(Qna.Type.APPLICATION);
        assertThat(saved.getSummaryId()).isEqualTo(10L);
        assertThat(saved.getAnswer()).isEqualTo("exponential backoff");
        verify(streamGateway, never()).sendError(anyLong(), anyString());
    }

    @Test
    void concurrentItemsGetDistinctCardNumbers() {
        relay(
                sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"),
                sse("start", "{\"item\":1,\"type\":\"ADVANCED\"}"),
                sse("done", "{\"item\":1,\"type\":\"ADVANCED\",\"question\":\"Q2\",\"answer\":\"A2\"}"),
                sse("done", "{\"item\":0,\"type\":\"CONCEPT\",\"question\":\"Q1\",\"answer\":\"A1\"}"));

        assertThat(stored).extracting(Qna::getCardId).containsExactly("qna_1_5_3", "qna_1_5_2");
    }

    @Test
    void cardNumberSkipsSavedAndReservedCards() {
        stored.add(Qna.builder().id(1L).lectureId(LECTURE).sectionIndex(SECTION).cardId("qna_1_5_4").type(Qna.Type.CONCEPT).question("old").answer("old").build());
        redisValues.put(RESERVATION_KEY, "7");

        relay(
                sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"),
                sse("done", "{\"item\":0,\"type\":\"CONCEPT\",\"question\":\"Q\",\"answer\":\"A\"}"));

        assertThat(stored.get(1).getCardId()).isEqualTo("qna_1_5_7");
        assertThat(redisValues.get(RESERVATION_KEY)).isEqualTo("8");
    }

    @Test
    void duplicateQuestionIsNotSavedAgain() {
        stored.add(Qna.builder().id(1L).lectureId(LECTURE).sectionIndex(SECTION).cardId("qna_1_5_2").type(Qna.Type.CONCEPT).question("Q").answer("A").build());

        relay(
                sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"),
                sse("done", "{\"item\":0,\"type\":\"CONCEPT\",\"question\":\"Q\",\"answer\":\"A\"}"));

        assertThat(stored).hasSize(1);
        ArgumentCaptor<QnaResponseDto> data = ArgumentCaptor.forClass(QnaResponseDto.class);
        verify(streamGateway).sendStreamComplete(eq(LECTURE), eq("qna_stream"), eq("qna_1_5_3"), data.capture());
        assertThat(data.getValue().getCardId()).isEqualTo("qna_1_5_2");
    }

    @Test
    void itemErrorNotifiesFailure() {
        relay(
                sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"),
                sse("error", "{\"item\":0,\"message\":\"timeout\"}"));

        verify(streamGateway).sendError(eq(LECTURE), anyString());
        assertThat(stored).isEmpty();
    }

    @Test
    void streamCutAfterStartNotifiesFailure() {
        service.relay(payload(), Flux.concat(
                Flux.just(sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}")),
                Flux.error(new IllegalStateException("connection reset")))).block();

        verify(streamGateway).sendError(eq(LECTURE), anyString());
    }

    @Test
    void failureBeforeAnyCardIsNotShownToUser() {
        service.relay(payload(), Flux.error(new IllegalStateException("RAG 검색 실패"))).block();

        verify(streamGateway, never()).sendError(anyLong(), anyString());
    }

    @Test
    void streamEndingWithoutDoneNotifiesFailure() {
        relay(sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"));

        verify(streamGateway).sendError(eq(LECTURE), anyString());
    }

    @Test
    void failureWhileSendingCompletedCardNotifiesFailure() {
        doThrow(new IllegalStateException("broker down")).when(streamGateway)
                .sendStreamComplete(eq(LECTURE), eq("qna_stream"), anyString(), any());

        relay(
                sse("start", "{\"item\":0,\"type\":\"CONCEPT\"}"),
                sse("done", "{\"item\":0,\"type\":\"CONCEPT\",\"question\":\"Q\",\"answer\":\"A\"}"));

        verify(streamGateway).sendError(eq(LECTURE), anyString());
    }
}
