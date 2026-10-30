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

    @Transactional
    public void handleSummaryCallback(SummaryCallbackDto dto) {
        log.info("[Callback] Summary received: lectureId={} section={} type={}",
                dto.lectureId(), dto.sectionIndex(), dto.phase());

        if (STATUS_TOO_SHORT.equalsIgnoreCase(dto.status())) {
            String message = dto.text() != null ? dto.text() : "요약을 생성하기에 강의가 너무 짧습니다.";
            streamGateway.sendError(dto.lectureId(), message);
            return;
        }

        SummaryPhase phase = SummaryPhase.from(dto.phase());
        Summary summary;

        if (phase == SummaryPhase.PARTIAL) {
            // 부분 요약은 화면 표시와 자동 카드 요청에만 쓰고 저장하지 않음. 그래서 ID가 없음
            summary = Summary.builder()
                    .lectureId(dto.lectureId())
                    .sectionIndex(dto.sectionIndex())
                    .text(dto.text())
                    .phase(phase)
                    .build();
            log.info("[Callback] PARTIAL summary: Skipping DB save.");
        } else {
            summary = summaryService.upsertFromCallback(dto);
            log.info("[Callback] FINAL summary saved: id={}", summary.getId());
        }

        streamGateway.sendSummary(summary);

        if (phase == SummaryPhase.FINAL) {
            try {
                log.info("[RAG Upsert] Sending FINAL summary: summaryId={}", summary.getId());
                aiServerClient.upsertSummaryText(summary.getLectureId(), summary);
            } catch (Exception e) {
                log.error("RAG Upsert failed", e);
            }

        } else {
            if (!autoCardProperties.isEnabled()) {
                log.info("[Partial Logic] Auto cards disabled: lectureId={} section={}",
                        dto.lectureId(), dto.sectionIndex());
                return;
            }
            cardRequestService.startAutoCards(dto.lectureId(), dto.sectionIndex(), dto.text());
        }
    }
}
