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
        int startSec;      // 섹션 시작 시간
        int lastEndSec;    // 섹션 내 마지막 전사의 endSec
        boolean partialDone;
        StringBuilder buffer;
    }

    public void onNewTranscript(Long lectureId, int sectionIndex, int startSec, int endSec, String text) {
        SectionState state = states.computeIfAbsent(lectureId, id -> {
            log.info("[SectionAgg] ✅ Init section state: lectureId={} section={}", lectureId, sectionIndex);
            streamGateway.sendSection(lectureId, sectionIndex);
            return new SectionState(sectionIndex, startSec, endSec, false, new StringBuilder());
        });

        // 섹션이 변경되었으면 이전 섹션의 FINAL 요약 보장 후 상태 초기화
        if (state.sectionIndex != sectionIndex) {
            log.info("[SectionAgg] 🔄 Section changed from {} to {}, ensuring FINAL summary", state.sectionIndex, sectionIndex);
            
            // 이전 섹션의 FINAL 요약이 아직 안 보내졌으면 지금 보내기
            if (!state.buffer.toString().trim().isEmpty()) {
                int elapsedSec = state.lastEndSec - state.startSec;
                log.info("[SectionAgg] 📤 Sending pending FINAL summary for section {}: elapsed={}s ({}~{}s)", 
                        state.sectionIndex, elapsedSec, state.startSec, state.lastEndSec);
                triggerAiSummary(lectureId, state, "FINAL");
            }
            
            // 새 섹션으로 초기화
            state = new SectionState(sectionIndex, startSec, endSec, false, new StringBuilder());
            states.put(lectureId, state);
            streamGateway.sendSection(lectureId, sectionIndex);
        } else {
            // 같은 섹션 내에서 lastEndSec 갱신
            state.lastEndSec = endSec;
        }

        state.buffer.append(' ').append(text);
        int elapsedSec = state.lastEndSec - state.startSec;

        // 1) 15초 도달 (Partial 요약 요청) - 30초 미만일 때만
        if (!state.partialDone && elapsedSec >= 15 && elapsedSec < 30) {
            log.info("[SectionAgg] ⏱️ Section {} reached 15s: PARTIAL summary", state.sectionIndex);
            triggerAiSummary(lectureId, state, "PARTIAL");
            state.partialDone = true;
        }

        // 2) 30초 도달 (Final 요약 요청 및 다음 섹션 준비)
        if (elapsedSec >= 30) {
            if (!state.partialDone) {
                log.info("[SectionAgg] ⏱️ Section {} reached 30s without PARTIAL: skipping to FINAL", state.sectionIndex);
            } else {
                log.info("[SectionAgg] ⏱️ Section {} reached 30s: FINAL summary", state.sectionIndex);
            }
            triggerAiSummary(lectureId, state, "FINAL");

            // 다음 섹션 준비 (startSec은 현재 섹션의 lastEndSec으로)
            SectionState next = new SectionState(state.sectionIndex + 1, state.lastEndSec, state.lastEndSec, false, new StringBuilder());
            states.put(lectureId, next);
            streamGateway.sendSection(lectureId, next.sectionIndex);
        }
    }

    // 핵심 로직: 직접 처리하지 않고 RagClient를 통해 AI 서버로 넘김
    private void triggerAiSummary(Long lectureId, SectionState state, String phase) {
        String sourceText = state.buffer.toString().trim();
        if (sourceText.isEmpty()) return;

        // 동적 시간 범위 사용
        int startSec = state.startSec;
        int endSec = state.lastEndSec;

        log.info("🚀 [AI Request] Summary Generation ({}): lectureId={} section={} time={}~{}s len={}",
                phase, lectureId, state.sectionIndex, startSec, endSec, sourceText.length());

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
