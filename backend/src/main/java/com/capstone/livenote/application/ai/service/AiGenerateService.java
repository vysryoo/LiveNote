package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.openai.service.OpenAiSummaryService;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiGenerateService {

    private final TranscriptService transcriptService;
    private final OpenAiSummaryService openAiSummaryService;
    private final SummaryService summaryService;
    private final AiRequestService aiRequestService;
    private final RagClient ragClient;
    private final StreamGateway streamGateway;

    /**
     * 프론트 요청에 의한 요약 생성 (15초 Partial / 30초 Final)
     */
    @Transactional
    public SummaryResponseDto generateSummary(Long lectureId, Integer sectionIndex, String phase) {
        log.info("📢 [AI Gen] Request received: lectureId={} section={} phase={}", lectureId, sectionIndex, phase);

        // 1. DB에서 해당 섹션의 전사 텍스트 조회
        String sourceText = transcriptService.getCombinedText(lectureId, sectionIndex);
        if (sourceText.isBlank()) {
            throw new IllegalArgumentException("해당 구간에 전사 내용이 없습니다.");
        }

        // 2. OpenAI 요약 수행
        String summaryText = openAiSummaryService.summarize(sourceText);

        SummaryResponseDto response;

        if ("partial".equalsIgnoreCase(phase)) {
            // === Partial Phase (15초) ===
            // DB 저장 X, 응답만 반환
            // 비동기로 Resource/QnA 카드 생성 요청 트리거
            aiRequestService.requestResourcesWithSummary(lectureId, 0L, sectionIndex, summaryText);
            aiRequestService.requestQnaWithSummary(lectureId, 0L, sectionIndex, summaryText);

            response = SummaryResponseDto.builder()
                    .lectureId(lectureId)
                    .sectionIndex(sectionIndex)
                    .startSec(sectionIndex * 30)
                    .endSec((sectionIndex * 30) + 30) // 임의 계산
                    .text(summaryText)
                    .phase(SummaryResponseDto.Phase.PARTIAL)
                    .build();

        } else {
            // === Final Phase (30초) ===
            // DB 저장 O
            Summary savedSummary = summaryService.createSectionSummary(lectureId, sectionIndex, summaryText);

            // RAG 업데이트 (비동기 권장)
            try {
                ragClient.upsertSummaryText(lectureId, savedSummary);
            } catch (Exception e) {
                log.warn("RAG upsert failed but ignoring", e);
            }

            // STOMP로 Final 확정 메시지 전송 (옵션, 프론트가 응답으로 처리하면 생략 가능하나 명세상 전송)
            streamGateway.sendSummary(lectureId, sectionIndex, summaryText, "final");

            response = SummaryResponseDto.from(savedSummary);
        }

        return response;
    }
}
