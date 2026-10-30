package com.capstone.livenote.card;

import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.ai.AiRequestPayloads.QnaGeneratePayload;
import com.capstone.livenote.global.stomp.StreamGateway;
import com.capstone.livenote.global.redis.RedisKeys;
import com.capstone.livenote.global.redis.RedisLock;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * AI 서버의 QnA 생성 스트림(SSE)을 받아 브라우저로 중계하고, 완성된 카드를 저장한다.
 *
 * 카드 번호는 생성이 시작될 때 예약해 서버 여러 대에서도 겹치지 않게 한다. 잠금은 번호 예약과 저장 순간에만 잡는다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class QnaStreamService {

    // 생성 중인 카드의 번호 예약을 기억하는 시간. 생성은 수 초 안에 끝나므로 넉넉하게 잡음
    private static final Duration RESERVATION_TTL = Duration.ofMinutes(10);

    private final AiServerClient aiServerClient;
    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;
    private final RedisLock redisLock;
    private final TransactionTemplate transactionTemplate;
    private final StringRedisTemplate redis;
    private final ObjectMapper objectMapper;

    /**
     * AI 서버에 QnA 생성을 요청하고, 생성되는 질문과 답변을 실시간으로 중계한다.
     *
     * 비동기로 진행되어 바로 반환한다. 생성 도중 실패하면 강의의 오류 토픽으로 알린다.
     *
     * @param payload QnA 생성 요청 본문
     * @param targetTypes 생성할 질문 유형. null이면 AI 서버 설정값 사용
     */
    public void generate(QnaGeneratePayload payload, List<String> targetTypes) {
        relay(payload, aiServerClient.streamQnaGeneration(payload, targetTypes)).subscribe();
    }

    /**
     * QnA 생성 이벤트 스트림을 처리하는 작업을 만든다. 구독해야 실행된다.
     *
     * @param payload QnA 생성 요청 본문
     * @param events AI 서버가 보낸 SSE 이벤트
     * @return 스트림을 끝까지 처리하면 완료되는 작업. 실패해도 오류로 끝나지 않음
     */
    Mono<Void> relay(QnaGeneratePayload payload, Flux<ServerSentEvent<String>> events) {
        Generation generation = new Generation(payload);
        return events
                // DB 저장과 Redis 잠금이 블로킹 호출이라 네트워크 스레드 대신 별도 스레드에서 처리
                .publishOn(Schedulers.boundedElastic())
                .doOnNext(generation::handle)
                .doOnComplete(generation::complete)
                .doOnError(generation::fail)
                .onErrorResume(e -> Mono.empty())
                .then();
    }

    private static final class Card {
        final String cardId;
        final String type;
        String question;
        boolean finished;

        Card(String cardId, String type) {
            this.cardId = cardId;
            this.type = type;
        }
    }

    /** 요청 한 건의 진행 상태. AI 서버의 item 번호별로 카드를 관리한다. */
    private final class Generation {
        private final QnaGeneratePayload payload;
        private final Map<Integer, Card> cards = new HashMap<>();
        private final long startedAt = System.nanoTime();
        private boolean firstEventMarked;
        private final Set<Integer> firstAnswerMarked = new HashSet<>();

        Generation(QnaGeneratePayload payload) {
            this.payload = payload;
        }

        void handle(ServerSentEvent<String> event) {
            JsonNode data = parse(event.data());
            int item = data.path("item").asInt();
            if (!firstEventMarked) {
                firstEventMarked = true;
                mark("first_event", null);
            }
            switch (String.valueOf(event.event())) {
                case "start" -> {
                    int cardIndex = reserveCardIndex(payload.lectureId(), payload.sectionIndex());
                    String cardId = CardIds.build("qna", payload.lectureId(), payload.sectionIndex(), cardIndex);
                    cards.put(item, new Card(cardId, data.path("type").asText()));
                }
                case "question" -> {
                    Card card = cards.get(item);
                    card.question = data.path("text").asText();
                    sendToken(card, "");
                    mark("item_question_sent", item);
                }
                case "answer" -> {
                    sendToken(cards.get(item), data.path("text").asText());
                    if (firstAnswerMarked.add(item)) {
                        mark("item_first_answer_sent", item);
                    }
                }
                case "done" -> {
                    Card card = cards.get(item);
                    Qna saved = saveCard(card, data.path("question").asText(), data.path("answer").asText());
                    streamGateway.sendStreamComplete(payload.lectureId(), "qna_stream", card.cardId,
                            QnaResponseDto.from(saved));
                    card.finished = true;
                    streamGateway.sendQna(payload.lectureId(), payload.sectionIndex(), findSectionQna());
                    mark("item_done_sent", item);
                }
                case "error" -> {
                    log.warn("QnA generation failed: lectureId={} section={} item={} message={}",
                            payload.lectureId(), payload.sectionIndex(), item, data.path("message").asText());
                    Card card = cards.get(item);
                    if (card != null) {
                        card.finished = true;
                        notifyFailure();
                    }
                }
                default -> log.debug("Ignoring QnA stream event: {}", event.event());
            }
        }

        void complete() {
            mark("completed", null);
            // 완료 이벤트 없이 끝난 카드는 화면에 생성 중으로 남지 않도록 실패로 알림
            if (cards.values().stream().anyMatch(card -> !card.finished)) {
                log.warn("QnA stream ended with unfinished cards: lectureId={} section={}",
                        payload.lectureId(), payload.sectionIndex());
                notifyFailure();
            }
        }

        void fail(Throwable error) {
            log.error("QnA stream failed: lectureId={} section={} error={}",
                    payload.lectureId(), payload.sectionIndex(), error.getMessage());
            // 생성을 시작하기 전에 실패한 경우(RAG 검색 실패 등)는 화면에 보인 카드가 없어 알리지 않음
            if (cards.values().stream().anyMatch(card -> !card.finished)) {
                notifyFailure();
            }
        }

        // AI 서버 요청 시점부터 브라우저로 중계한 시점까지의 경과 시간. 스트리밍 효과 측정용
        private void mark(String stage, Integer item) {
            log.info("[timing] kind=qna_relay lectureId={} section={} stage={} item={} elapsedMs={}",
                    payload.lectureId(), payload.sectionIndex(), stage, item,
                    (System.nanoTime() - startedAt) / 1_000_000);
        }

        private void sendToken(Card card, String token) {
            streamGateway.sendStreamToken(payload.lectureId(), "qna_stream", card.cardId, token, card.question);
        }

        private void notifyFailure() {
            streamGateway.sendError(payload.lectureId(), "qna generation failed");
        }

        private Qna saveCard(Card card, String question, String answer) {
            return redisLock.call(RedisKeys.qnaLock(payload.lectureId(), payload.sectionIndex()),
                    () -> transactionTemplate.execute(status -> {
                        // 같은 질문·답변이 이미 있으면 새로 저장하지 않고 기존 카드를 완료 데이터로 사용
                        List<Qna> existing = qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                                payload.lectureId(), payload.sectionIndex());
                        String signature = CardIds.signature(question, answer);
                        for (Qna qna : existing) {
                            if (CardIds.signature(qna.getQuestion(), qna.getAnswer()).equals(signature)) {
                                return qna;
                            }
                        }
                        Long summaryId = payload.summaryId();
                        return qnaRepository.save(Qna.builder()
                                .lectureId(payload.lectureId())
                                .summaryId(summaryId == null || summaryId == 0L ? null : summaryId)
                                .sectionIndex(payload.sectionIndex())
                                .cardId(card.cardId)
                                .type(Qna.Type.from(card.type))
                                .question(question)
                                .answer(answer)
                                .build());
                    }));
        }

        private List<QnaResponseDto> findSectionQna() {
            return qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                            payload.lectureId(), payload.sectionIndex())
                    .stream()
                    .map(QnaResponseDto::from)
                    .toList();
        }
    }

    // 저장된 카드와 생성 중인 카드의 번호를 모두 피해 다음 번호를 정함
    private int reserveCardIndex(Long lectureId, Integer sectionIndex) {
        String reservationKey = RedisKeys.qnaNextCard(lectureId, sectionIndex);
        return redisLock.call(RedisKeys.qnaLock(lectureId, sectionIndex), () -> {
            List<Qna> existing = qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(lectureId, sectionIndex);
            String reserved = redis.opsForValue().get(reservationKey);
            int next = Math.max(CardIds.nextIndex(existing.stream().map(Qna::getCardId).toList()),
                    reserved == null ? 0 : Integer.parseInt(reserved));
            redis.opsForValue().set(reservationKey, String.valueOf(next + 1), RESERVATION_TTL);
            return next;
        });
    }

    private JsonNode parse(String json) {
        try {
            return objectMapper.readTree(json == null ? "{}" : json);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("invalid QnA stream event data", e);
        }
    }
}
