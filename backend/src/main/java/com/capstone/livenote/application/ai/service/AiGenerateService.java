package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
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
    private final SummaryService summaryService;
    private final RagClient ragClient;

    /**
     * 프론트 요청에 의한 요약 생성 트리거
     *  - 실제 요약 생성은 AI 서버(/summary/generate)가 하고
     *  - 결과는 /api/ai/callback?type=summary 로 돌아옴
     */
    @Transactional(readOnly = true)
    public void generateSummary(Long lectureId, Integer sectionIndex, String phase) {
        log.info("📢 [AI Gen] Summary request: lectureId={} section={} phase={}",
                lectureId, sectionIndex, phase);

        // 1. 해당 섹션 전사 텍스트 합치기
        String sourceText = transcriptService.getCombinedText(lectureId, sectionIndex);
        if (sourceText == null || sourceText.isBlank()) {
            throw new IllegalArgumentException("해당 구간에 전사 내용이 없습니다.");
        }

        // 2. 이미 요약이 있다면 그 id를 넘겨줌(없으면 null)
        Long summaryId = summaryService.findByLectureAndSection(lectureId, sectionIndex)
                .map(Summary::getId)
                .orElse(null);

        int startSec = sectionIndex * 30;
        int endSec   = startSec + 30;

        // 3. AI 서버에 요약 생성 요청만 보냄 (실제 저장/푸시는 콜백에서 처리)
        ragClient.requestSummaryGeneration(
                lectureId,
                summaryId,                      // null 가능
                sectionIndex,
                startSec,
                endSec,
                phase != null ? phase : "FINAL",
                sourceText
        );

    }
}
