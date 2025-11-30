// com.capstone.livenote.application.ai.service.SummaryCallbackService

package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
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

    @Transactional
    public void handleSummaryCallback(SummaryCallbackDto dto) {
        log.info("📝 [Callback] Summary received: lectureId={} section={} type={}",
                dto.getLectureId(), dto.getSectionIndex(), dto.getPhase());

        if (STATUS_TOO_SHORT.equalsIgnoreCase(dto.getStatus())) {
            String message = dto.getText() != null ? dto.getText() : "요약을 생성하기에 강의가 너무 짧습니다.";
            log.info("⏭️  [Summary] Skipping DB save due to short transcript: lectureId={} section={}",
                    dto.getLectureId(), dto.getSectionIndex());
            streamGateway.sendError(dto.getLectureId(), message);
            return;
        }

        SummaryPhase phase = SummaryPhase.from(dto.getPhase());

        // 1. DB 저장
        // SummaryService.upsertFromCallback 구현 확인 완료 (기존 내용 있으면 업데이트)
        Summary summary = summaryService.upsertFromCallback(dto);

        // 2. 프론트엔드 실시간 전송 (STOMP)
        // StreamGateway에 복구한 메서드 사용
        streamGateway.sendSummary(
                summary.getLectureId(),
                summary.getSectionIndex(),
                summary.getText(),
                dto.getPhase() // "partial" or "final"
        );

        if (phase == SummaryPhase.FINAL) {
            // 3. ✅ Final 요약인 경우에만 RAG 업서트
            try {
                log.info("🗂️ [RAG Upsert] Sending FINAL summary to Vector DB: summaryId={}", summary.getId());
                ragClient.upsertSummaryText(summary.getLectureId(), summary);
            } catch (Exception e) {
                log.error("❌ RAG Upsert failed: {}", e.getMessage());
                // RAG 실패가 메인 로직을 중단시키지 않도록 예외 처리
            }

            return;
        }

        // 4. Partial 단계에서는 즉시 AI 추천/QnA 요청
        aiRequestService.requestResourcesWithSummary(
                summary.getLectureId(),
                summary.getId(),
                summary.getSectionIndex(),
                summary.getText()
        );
        aiRequestService.requestQnaWithSummary(
                summary.getLectureId(),
                summary.getId(),
                summary.getSectionIndex(),
                summary.getText()
        );
    }
}
