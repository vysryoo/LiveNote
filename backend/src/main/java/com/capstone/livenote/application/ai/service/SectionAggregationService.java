package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.AiServerClient;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import com.capstone.livenote.domain.transcript.service.RecordingStateStore;
import com.capstone.livenote.domain.transcript.service.RecordingStateStore.SectionState;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 섹션 단위 집계 -> AI 서버로 요약 요청 트리거
 * (결과는 비동기 콜백으로 수신되므로, 여기서는 요청만 보내고 끝냄)
 *
 * 섹션 상태는 {@link RecordingStateStore}(Redis)에 두어 서버 여러 대와 재시작 후에도 이어진다.
 * 상태를 읽고 쓰는 두 메서드는 강의 단위 잠금 안에서 호출해야 한다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SectionAggregationService {

    static final int PARTIAL_SEC = 15;
    /** 섹션 하나의 길이(초) */
    public static final int SECTION_SEC = 30;

    private final AiServerClient aiServerClient;
    private final TranscriptRepository transcriptRepository;
    private final RecordingStateStore stateStore;
    private final StreamGateway streamGateway;

    /**
     * 새 전사가 속할 섹션을 정하고 섹션 상태를 갱신한다.
     *
     * 최종 요약을 요청한 섹션이거나 섹션 시작으로부터 30초 이상 지난 전사는 다음 섹션으로 넘긴다.
     * 최종 요약 없이 넘어가는 섹션은 이때 최종 요약을 요청한다.
     *
     * @param lectureId 강의 ID
     * @param startSec 전사 시작 시각(초, 강의 전체 기준)
     * @param endSec 전사 끝 시각(초, 강의 전체 기준)
     * @return 전사가 속할 섹션 번호
     */
    public int assignSection(Long lectureId, int startSec, int endSec) {
        SectionState current = stateStore.findSection(lectureId).orElseGet(() -> restoreSection(lectureId));

        SectionState next;
        if (current == null) {
            log.info("[SectionAgg] Init section state: lectureId={} section=0", lectureId);
            next = SectionState.start(0, startSec, endSec);
            streamGateway.sendSection(lectureId, next.index());
        } else if (current.finalRequested() || startSec - current.startSec() >= SECTION_SEC) {
            next = SectionState.start(current.index() + 1, startSec, endSec);
            if (!current.finalRequested()) {
                log.info("[SectionAgg] Section {} closed without FINAL: sending FINAL", current.index());
                requestSummary(lectureId, current, "FINAL");
                streamGateway.sendSection(lectureId, next.index());
            }
        } else {
            next = current.withLastEndSec(Math.max(current.lastEndSec(), endSec));
        }

        stateStore.saveSection(lectureId, next);
        return next.index();
    }

    /**
     * 전사 저장 후 섹션 길이가 15초, 30초에 도달했으면 부분·최종 요약을 요청한다.
     *
     * 최종 요약을 요청하면 다음 섹션 번호를 실시간으로 알린다. 다음 전사부터 그 섹션에 속한다.
     *
     * @param lectureId 강의 ID
     */
    public void onTranscriptSaved(Long lectureId) {
        SectionState state = stateStore.findSection(lectureId).orElse(null);
        if (state == null) {
            return;
        }
        int elapsedSec = state.elapsedSec();
        SectionState next = state;

        if (!state.partialRequested() && elapsedSec >= PARTIAL_SEC && elapsedSec < SECTION_SEC) {
            log.info("[SectionAgg] Section {} reached {}s: PARTIAL summary", state.index(), PARTIAL_SEC);
            requestSummary(lectureId, state, "PARTIAL");
            next = next.withPartialRequested();
        }

        if (!state.finalRequested() && elapsedSec >= SECTION_SEC) {
            log.info("[SectionAgg] Section {} reached {}s: FINAL summary", state.index(), SECTION_SEC);
            requestSummary(lectureId, state, "FINAL");
            next = next.withFinalRequested();
            streamGateway.sendSection(lectureId, state.index() + 1);
        }

        if (!next.equals(state)) {
            stateStore.saveSection(lectureId, next);
        }
    }

    // Redis에 상태가 없으면(첫 전사, 서버 재시작 후 만료, Redis 초기화) DB의 마지막 섹션에서 이어 감
    private SectionState restoreSection(Long lectureId) {
        Integer lastIndex = transcriptRepository.findMaxSectionIndexByLectureId(lectureId);
        if (lastIndex == null) {
            return null;
        }
        List<Transcript> transcripts =
                transcriptRepository.findByLectureIdAndSectionIndexOrderByStartSecAsc(lectureId, lastIndex);
        int startSec = transcripts.get(0).getStartSec();
        int lastEndSec = transcripts.stream().mapToInt(Transcript::getEndSec).max().orElse(startSec);
        int elapsedSec = lastEndSec - startSec;
        log.info("[SectionAgg] Restored section state from DB: lectureId={} section={} range={}~{}s",
                lectureId, lastIndex, startSec, lastEndSec);
        return new SectionState(lastIndex, startSec, lastEndSec,
                elapsedSec >= PARTIAL_SEC, elapsedSec >= SECTION_SEC);
    }

    // 핵심 로직: 직접 처리하지 않고 AiServerClient를 통해 AI 서버로 넘김
    private void requestSummary(Long lectureId, SectionState state, String phase) {
        String sourceText = transcriptRepository
                .findByLectureIdAndSectionIndexOrderByStartSecAsc(lectureId, state.index())
                .stream()
                .map(Transcript::getText)
                .collect(Collectors.joining(" "))
                .trim();
        if (sourceText.isEmpty()) return;

        log.info("[AI Request] Summary Generation ({}): lectureId={} section={} time={}~{}s len={}",
                phase, lectureId, state.index(), state.startSec(), state.lastEndSec(), sourceText.length());

        // 비동기 요청 전송 (결과는 나중에 CallbackService로 옴)
        aiServerClient.requestSummaryGeneration(
                lectureId,
                null, // 신규 생성이므로 ID 없음
                state.index(),
                state.startSec(),
                state.lastEndSec(),
                phase,
                sourceText
        );
    }
}
