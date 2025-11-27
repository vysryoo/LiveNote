package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.openai.service.OpenAiSummaryService;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.summary.service.SummaryService;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 섹션 단위 집계 + 요약
 *  - TranscriptService.saveFromStt(...) 에서 호출됨
 *  - 강의(lectureId)별로 현재 섹션 상태를 메모리에 들고 있다가
 *      * 15초 누적 시: partial(임시) 요약 생성 + 2개 자료/2개 QnA AI 요청
 *      * 30초 누적 시: final(최종) 요약 생성 + Summary 엔티티 저장 + 프론트로 푸시
 */
@Service
@Slf4j
public class SectionAggregationService {

    private final OpenAiSummaryService openAiSummaryService;
    private final SummaryService summaryService;
    private final SummaryRepository summaryRepository;
    private final RagClient ragClient;
    private final AiRequestService aiRequestService;
    private final StreamGateway streamGateway;

    public SectionAggregationService(
            OpenAiSummaryService openAiSummaryService,
            SummaryService summaryService,
            SummaryRepository summaryRepository,
            RagClient ragClient,
            AiRequestService aiRequestService,
            @Lazy StreamGateway streamGateway
    ) {
        this.openAiSummaryService = openAiSummaryService;
        this.summaryService = summaryService;
        this.summaryRepository = summaryRepository;
        this.ragClient = ragClient;
        this.aiRequestService = aiRequestService;
        this.streamGateway = streamGateway;
    }

    private final Map<Long, SectionState> states = new ConcurrentHashMap<>();

    @Getter
    @AllArgsConstructor
    private static class SectionState {
        int sectionIndex; // 현재 섹션 번호
        int elapsedSec; // 섹션 시작 이후 누적된 시간
        boolean partialDone; // 15초 요약을 보냈는지 여부
        StringBuilder buffer; // 전사 텍스트 누적 버퍼
    }


    public void onNewTranscript(Long lectureId, int sectionIndex, int startSec, int endSec, String text) {
        int delta = endSec - startSec;

        // 강의별 섹션 상태 조회/초기화
        SectionState state = states.computeIfAbsent(
                lectureId,
                id -> {
                    log.info("[SectionAgg] ✅ Initializing new section state for lectureId={} sectionIndex={}",
                            lectureId, sectionIndex);
                    return new SectionState(sectionIndex, 0, false, new StringBuilder());
                }
        );

        // 섹션이 바뀔면 새 상태로 초기화
        if (state.sectionIndex != sectionIndex) {
            log.info("[SectionAgg] 🔄 Section changed: lectureId={} from section {} to {}",
                    lectureId, state.sectionIndex, sectionIndex);
            state = new SectionState(sectionIndex, 0, false, new StringBuilder());
            states.put(lectureId, state);
        }

        state.elapsedSec += delta;
        state.buffer.append(' ').append(text);

        log.debug("[SectionAgg] lectureId={} section={} elapsed={}s",
                lectureId, state.sectionIndex, state.elapsedSec);

        // 1) 15초 도달 & 아직 partial 발행 안 했으면 → partial 처리
        if (!state.partialDone && state.elapsedSec >= 15) {
            handlePartial(lectureId, state);
            state.partialDone = true;
        }

        // 2) 30초 도달 → 섹션 확정 & final 처리
        if (state.elapsedSec >= 30) {
            handleFinal(lectureId, state);

            // 다음 섹션으로 초기화
            SectionState next = new SectionState(
                    state.sectionIndex + 1,
                    0,
                    false,
                    new StringBuilder()
            );
            states.put(lectureId, next);
        }
    }

    /**
     * 15초 시점 처리:
     *  - OpenAI로 임시 요약(partial) 생성
     *  - 요약은 DB에 저장하지 않음
     *  - STOMP로 프론트에 partial 요약 push
     *  - 동시에 2개 자료 / 2개 QnA 생성 요청을 AI 서버(RAG)에 보냄
     */
    private void handlePartial(Long lectureId, SectionState state) {
        String text = state.buffer.toString();

        String partialSummary = openAiSummaryService.summarize(text);

        log.info("[SectionAgg] ✅ PARTIAL summary created: lectureId={} section={} length={}",
                lectureId, state.sectionIndex, partialSummary.length());

        // STOMP로 프론트에 partial 요약 전송
        streamGateway.sendSummary(lectureId, state.sectionIndex, partialSummary, "partial");
        log.info("[SectionAgg] 📤 PARTIAL summary pushed via STOMP: lectureId={} section={}",
                lectureId, state.sectionIndex);

        // partial 기반 자료 2개 / QnA 2개 요청
        aiRequestService.requestResourcesWithSummary(
                lectureId,
                null,
                state.sectionIndex,
                partialSummary
        );
        aiRequestService.requestQnaWithSummary(
                lectureId,
                null,
                state.sectionIndex,
                partialSummary
        );
    }

    /**
     * 30초 시점 처리:
     *  - 하나의 섹션을 확정하고 섹션 전체 텍스트를 요약
     *  - Summary 엔티티로 DB에 저장
     *  - STOMP로 프론트에 final 요약 push
     *  - RAG 인덱스에 업서트
     */
    private void handleFinal(Long lectureId, SectionState state) {
        String text = state.buffer.toString();

        String finalSummary = openAiSummaryService.summarize(text);

        log.info("[SectionAgg] ✅ FINAL summary created: lectureId={} section={} length={}",
                lectureId, state.sectionIndex, finalSummary.length());

        // DB에 섹션 요약 저장
        Summary summary = summaryService.createSectionSummary(
                lectureId,
                state.sectionIndex,
                finalSummary
        );
        log.info("[SectionAgg] 💾 FINAL summary saved to DB: id={} lectureId={} section={}",
                summary.getId(), lectureId, state.sectionIndex);

        // STOMP로 프론트에 final 요약 전송
        streamGateway.sendSummary(lectureId, state.sectionIndex, finalSummary, "final");
        log.info("[SectionAgg] 📤 FINAL summary pushed via STOMP: lectureId={} section={}",
                lectureId, state.sectionIndex);

        // 최종 요약을 RAG 인덱스에 업서트
        ragClient.upsertSummaryText(lectureId, summary);

    }

}
