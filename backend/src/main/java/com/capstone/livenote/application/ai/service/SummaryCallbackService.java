// com.capstone.livenote.application.ai.service.SummaryCallbackService

package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ai.config.AiAutoCardProperties;
import com.capstone.livenote.application.ai.dto.SummaryCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;
import com.capstone.livenote.domain.summary.service.SummaryService;
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
    private final AiRequestService aiRequestService;
    private final RagClient ragClient;
    private final AiAutoCardProperties autoCardProperties;

    @Transactional
    public void handleSummaryCallback(SummaryCallbackDto dto) {
        log.info("📝 [Callback] Summary received: lectureId={} section={} type={}",
                dto.getLectureId(), dto.getSectionIndex(), dto.getPhase());

        // 너무 짧은 전사 처리
        if (STATUS_TOO_SHORT.equalsIgnoreCase(dto.getStatus())) {
            String message = dto.getText() != null ? dto.getText() : "요약을 생성하기에 강의가 너무 짧습니다.";
            streamGateway.sendError(dto.getLectureId(), message);
            return;
        }

        SummaryPhase phase = SummaryPhase.from(dto.getPhase());
        Summary summary;

        // 2. Phase에 따른 저장 로직 분기 (핵심 수정!)
        if (phase == SummaryPhase.PARTIAL) {
            // PARTIAL: DB 저장 안 함 (임시 객체 생성)
            // ID는 null로 설정됨
            summary = Summary.builder()
                    .lectureId(dto.getLectureId())
                    .sectionIndex(dto.getSectionIndex())
                    .text(dto.getText())
                    .phase(phase)
                    .build();
            log.info("⏭️ [Callback] PARTIAL summary: Skipping DB save.");
        } else {
            // FINAL: DB 저장 (Upsert)
            summary = summaryService.upsertFromCallback(dto);
            log.info("💾 [Callback] FINAL summary saved: id={}", summary.getId());
        }

        // 2. 프론트엔드 실시간 전송 (STOMP)
        streamGateway.sendSummary(summary);

        // 3. 단계별 분기 처리
        if (phase == SummaryPhase.FINAL) {
            // FINAL 단계
            try {
                log.info("🗂️ [RAG Upsert] Sending FINAL summary: summaryId={}", summary.getId());
                ragClient.upsertSummaryText(summary.getLectureId(), summary);
            } catch (Exception e) {
                log.error("❌ RAG Upsert failed", e);
            }

        } else {
            // PARTIAL 단계
            if (!autoCardProperties.isEnabled()) {
                log.info("[Partial Logic] Auto cards disabled: lectureId={} section={}",
                        dto.getLectureId(), dto.getSectionIndex());
                return;
            }
            log.info("🚀 [Partial Logic] Requesting initial 2 QnA & 2 Resources");

            // limit=2 로 요청. 한쪽 요청이 실패해도 다른 쪽과 요약 저장 결과에는 영향을 주지 않음
            try {
                aiRequestService.requestResourcesWithSummary(
                        dto.getLectureId(), null, dto.getSectionIndex(), dto.getText(), 2
                );
            } catch (Exception e) {
                log.error("❌ Resource request after PARTIAL summary failed: lectureId={} section={} error={}",
                        dto.getLectureId(), dto.getSectionIndex(), e.getMessage());
            }
            try {
                aiRequestService.requestQnaWithSummary(
                        dto.getLectureId(), null, dto.getSectionIndex(), dto.getText(), 2
                );
            } catch (Exception e) {
                log.error("❌ QnA request after PARTIAL summary failed: lectureId={} section={} error={}",
                        dto.getLectureId(), dto.getSectionIndex(), e.getMessage());
            }
        }
    }
}
