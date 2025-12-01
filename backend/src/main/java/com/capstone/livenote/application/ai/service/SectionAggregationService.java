package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.context.annotation.Lazy;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 섹션 단위 집계 -> AI 서버로 요약 요청 트리거
 * (결과는 비동기 콜백으로 수신되므로, 여기서는 요청만 보내고 끝냄)
 */
@Service
@Slf4j
public class SectionAggregationService {

    private final RagClient ragClient;
    private final SummaryService summaryService;
    private final StreamGateway streamGateway;

    public SectionAggregationService(RagClient ragClient, SummaryService summaryService, @Lazy StreamGateway streamGateway) {
        this.ragClient = ragClient;
        this.summaryService = summaryService;
        this.streamGateway = streamGateway;
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
            streamGateway.sendSection(lectureId, sectionIndex);
            return new SectionState(sectionIndex, 0, false, new StringBuilder());
        });

        // 섹션이 변경되었으면 이전 섹션의 FINAL 요약 보장 후 상태 초기화
        if (state.sectionIndex != sectionIndex) {
            log.info("[SectionAgg] 🔄 Section changed from {} to {}, ensuring FINAL summary", state.sectionIndex, sectionIndex);
            
            // 이전 섹션의 FINAL 요약이 아직 안 보내졌으면 지금 보내기
            if (state.elapsedSec > 0 && !state.buffer.toString().trim().isEmpty()) {
                log.info("[SectionAgg] 📤 Sending pending FINAL summary for section {}: elapsedSec={}", 
                        state.sectionIndex, state.elapsedSec);
                triggerAiSummary(lectureId, state, "FINAL");
            }
            
            // 새 섹션으로 초기화
            state = new SectionState(sectionIndex, 0, false, new StringBuilder());
            states.put(lectureId, state);
            streamGateway.sendSection(lectureId, sectionIndex);
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
            streamGateway.sendSection(lectureId, next.sectionIndex);
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
