package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.openai.service.OpenAiSummaryService;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.service.SummaryService;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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
@RequiredArgsConstructor
@Slf4j
public class SectionAggregationService {

    private final OpenAiSummaryService openAiSummaryService;
    private final SummaryService summaryService;
    private final RagClient ragClient;
    private final AiRequestService aiRequestService;
    //private final StreamGateway streamGateway;

    private final Map<Long, SectionState> states = new ConcurrentHashMap<>();

    @Getter
    @AllArgsConstructor
    private static class SectionState {
        int sectionIndex; // 현재 섹션 번호
        int elapsedSec; // 섹션 시작 이후 누적된 시간
        boolean partialDone; // 15초 요약을 보냈는지 여부
        StringBuilder buffer; // 전사 텍스트 누적 버퍼
    }


    public void onNewTranscript(Long lectureId, int startSec, int endSec, String text) {
        int delta = endSec - startSec; // 이번 청크의 길이(초) – 5초 고정이라면 5

        // 강의별 섹션 상태 조회/초기화
        SectionState state = states.computeIfAbsent(
                lectureId,
                id -> new SectionState(0, 0, false, new StringBuilder())
        );

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
     *  - 동시에 2개 자료 / 2개 QnA 생성 요청을 AI 서버(RAG)에 보냄
     *  - (실시간 WebSocket 푸시는 AI 콜백에서 처리)
     */
    private void handlePartial(Long lectureId, SectionState state) {
        String text = state.buffer.toString();

        String partialSummary = openAiSummaryService.summarize(text);

        log.info("[SectionAgg] PARTIAL summary created: lectureId={} section={}",
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
     *  - 최종 요약은 나중에 API/콜백을 통해 프론트에 제공
     */
    private void handleFinal(Long lectureId, SectionState state) {
        String text = state.buffer.toString();

        String finalSummary = openAiSummaryService.summarize(text);

        log.info("[SectionAgg] FINAL summary created: lectureId={} section={}",
                lectureId, state.sectionIndex);

        // DB에 섹션 요약 저장
        Summary summary = summaryService.createSectionSummary(
                lectureId,
                state.sectionIndex,
                finalSummary
        );

        // 최종 요약을 RAG 인덱스에 업서트
        ragClient.upsertSummaryText(lectureId, summary);

    }

}
