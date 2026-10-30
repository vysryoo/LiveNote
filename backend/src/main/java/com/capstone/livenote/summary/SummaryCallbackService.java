package com.capstone.livenote.summary;

import com.capstone.livenote.card.CardRequestService;
import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.ai.AiAutoCardProperties;
import com.capstone.livenote.ai.SummaryCallbackDto;
import com.capstone.livenote.global.stomp.StreamGateway;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * AI 서버의 요약 콜백을 처리한다.
 *
 * 부분 요약은 화면 전송과 자동 카드 요청에, 최종 요약은 저장, 화면 전송, RAG 업서트에 쓴다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class SummaryCallbackService {

    private static final String STATUS_TOO_SHORT = "TOO_SHORT";

    private final SummaryService summaryService;
    private final StreamGateway streamGateway;
    private final CardRequestService cardRequestService;
    private final AiServerClient aiServerClient;
    private final AiAutoCardProperties autoCardProperties;

    /**
     * 요약 콜백 한 건을 처리한다.
     *
     * 전사가 너무 짧다는 응답({@code status=TOO_SHORT})이면 오류 토픽으로 알리고 끝낸다.
     * RAG 업서트와 자동 카드 요청이 실패하면 로그로만 남긴다.
     *
     * @param dto 요약 콜백 본문
     */
    @Transactional
    public void handleSummaryCallback(SummaryCallbackDto dto) {
        log.info("[Callback] Summary received: lectureId={} section={} type={}",
                dto.lectureId(), dto.sectionIndex(), dto.phase());

        if (STATUS_TOO_SHORT.equalsIgnoreCase(dto.status())) {
            String message = dto.text() != null ? dto.text() : "요약을 생성하기에 강의가 너무 짧습니다.";
            streamGateway.sendError(dto.lectureId(), message);
            return;
        }

        if (SummaryPhase.from(dto.phase()) == SummaryPhase.PARTIAL) {
            handlePartial(dto);
        } else {
            handleFinal(dto);
        }
    }

    // 부분 요약은 화면 표시와 자동 카드 요청에만 쓰고 저장하지 않음. 그래서 ID가 없음
    private void handlePartial(SummaryCallbackDto dto) {
        Summary summary = Summary.builder()
                .lectureId(dto.lectureId())
                .sectionIndex(dto.sectionIndex())
                .text(dto.text())
                .phase(SummaryPhase.PARTIAL)
                .build();
        log.info("[Callback] PARTIAL summary: Skipping DB save.");
        streamGateway.sendSummary(summary);

        if (!autoCardProperties.isEnabled()) {
            log.info("[Partial Logic] Auto cards disabled: lectureId={} section={}",
                    dto.lectureId(), dto.sectionIndex());
            return;
        }
        cardRequestService.startAutoCards(dto.lectureId(), dto.sectionIndex(), dto.text());
    }

    private void handleFinal(SummaryCallbackDto dto) {
        Summary summary = summaryService.upsertFromCallback(dto);
        log.info("[Callback] FINAL summary saved: id={}", summary.getId());
        streamGateway.sendSummary(summary);

        try {
            log.info("[RAG Upsert] Sending FINAL summary: summaryId={}", summary.getId());
            aiServerClient.upsertSummaryText(summary.getLectureId(), summary);
        } catch (Exception e) {
            log.error("RAG Upsert failed", e);
        }
    }
}
