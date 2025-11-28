package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 섹션 단위 집계 -> AI 서버로 요약 요청 트리거
 * (결과는 비동기 콜백으로 수신되므로, 여기서는 요청만 보내고 끝냅니다)
 */
@Service
@Slf4j
public class SectionAggregationService {

    private final RagClient ragClient;

    // 불필요한 의존성(OpenAiSummaryService, SummaryService 등) 모두 제거
    public SectionAggregationService(RagClient ragClient) {
        this.ragClient = ragClient;
    }

    private final Map<Long, SectionState> states = new ConcurrentHashMap<>();

    @Getter
    @AllArgsConstructor
    private static class SectionState {
        int sectionIndex;
        int elapsedSec;
        boolean partialDone;
        StringBuilder buffer;
    }

    public void onNewTranscript(Long lectureId, int sectionIndex, int startSec, int endSec, String text) {
        int delta = endSec - startSec;

        SectionState state = states.computeIfAbsent(lectureId, id -> {
            log.info("[SectionAgg] ✅ Init section state: lectureId={} section={}", lectureId, sectionIndex);
            return new SectionState(sectionIndex, 0, false, new StringBuilder());
        });

        // 섹션이 변경되었으면 상태 초기화
        if (state.sectionIndex != sectionIndex) {
            // log.info("[SectionAgg] 🔄 Section changed...");
            state = new SectionState(sectionIndex, 0, false, new StringBuilder());
            states.put(lectureId, state);
        }

        state.elapsedSec += delta;
        state.buffer.append(' ').append(text);

        // 1) 15초 도달 (Partial 요약 요청)
        if (!state.partialDone && state.elapsedSec >= 15) {
            triggerAiSummary(lectureId, state, "PARTIAL");
            state.partialDone = true;
        }

        // 2) 30초 도달 (Final 요약 요청)
        if (state.elapsedSec >= 30) {
            triggerAiSummary(lectureId, state, "FINAL");

            // 다음 섹션 준비
            SectionState next = new SectionState(state.sectionIndex + 1, 0, false, new StringBuilder());
            states.put(lectureId, next);
        }
    }

    // 핵심 로직: 직접 처리하지 않고 RagClient를 통해 AI 서버로 넘김
    private void triggerAiSummary(Long lectureId, SectionState state, String phase) {
        String sourceText = state.buffer.toString().trim();
        if (sourceText.isEmpty()) return;

        int startSec = state.sectionIndex * 30;
        int endSec = startSec + 30;

        log.info("🚀 [AI Request] Summary Generation ({}): lectureId={} section={} len={}",
                phase, lectureId, state.sectionIndex, sourceText.length());

        // 비동기 요청 전송 (결과는 나중에 CallbackService로 옴)
        ragClient.requestSummaryGeneration(
                lectureId,
                null, // 신규 생성이므로 ID 없음
                state.sectionIndex,
                startSec,
                endSec,
                phase,
                sourceText
        );
    }
}