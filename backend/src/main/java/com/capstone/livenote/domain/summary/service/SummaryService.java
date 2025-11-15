package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.openai.service.OpenAiSummaryService;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Service
@RequiredArgsConstructor
public class SummaryService {


    private static final int SECTION_SECONDS = 60;     // 1분 단위 요약이면 60
    private static final int MAX_SUMMARY_LEN = 500;    // 로컬 요약용 글자 제한 (임시)

    private final SummaryRepository summaryRepository;
    private final TranscriptRepository transcriptRepository;
    private final LectureRepository lectureRepository;
    private final OpenAiSummaryService openAiSummaryService;
    private final RagClient ragClient;
    //private final StreamGateway streamGateway;

    // 강의 요약 리스트 조회
    @Transactional(readOnly = true)
    public List<Summary> findSince(Long lectureId, Integer sinceSection) {
        if (sinceSection == null) return summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
        return summaryRepository.findByLectureIdAndSectionIndexGreaterThanOrderBySectionIndexAsc(lectureId, sinceSection);
    }

    // 요약 생성
    /**
     * 30초 윈도우 [startSec, endSec) 기반 요약 생성/업서트
     *
     * 플로우:
     * 1. 해당 구간의 전사 수집
     * 2. OpenAI GPT로 요약 생성
     * 3. DB 저장 (upsert)
     * 4. WebSocket 전송
     * 5. AI 서버로 RAG 업서트 + QnA/추천자료 생성 요청
     */
    @Transactional
    public Summary summarizeWindow(Long lectureId, int startSec, int endSec) {
        int sectionIndex = startSec / 30;

        // 1) 강의 언어 조회
        String language = lectureRepository.findById(lectureId)
                .map(Lecture::getSttLanguage)
                .orElse("ko");

        // 2) 윈도우 내 전사 모으기
        var transcripts = transcriptRepository.findByLectureIdAndStartSecBetweenOrderByStartSecAsc(
                lectureId, startSec, Math.max(startSec, endSec - 1));

        if (transcripts.isEmpty()) {
            return summaryRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .orElse(null);
        }

        // 3) 전사 텍스트 결합
        int winStart = transcripts.stream().mapToInt(Transcript::getStartSec).min().orElse(startSec);
        int winEnd = transcripts.stream().mapToInt(Transcript::getEndSec).max().orElse(endSec);
        String rawText = String.join(" ", transcripts.stream().map(Transcript::getText).toList());

        // 4) OpenAI GPT로 요약 생성
        //String summaryText = openAiSummaryService.summarize(rawText, language);

        String summaryText = openAiSummaryService.summarize(rawText);

        System.out.println("[SummaryService] Summary generated for section " + sectionIndex);

        // 5) 요약 저장 (upsert)
        var existing = summaryRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
        Summary saved = existing.map(s -> {
            s.setStartSec(Math.min(s.getStartSec(), winStart));
            s.setEndSec(Math.max(s.getEndSec(), winEnd));
            s.setText(summaryText);
            return s;
        }).orElseGet(() -> Summary.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .startSec(winStart)
                .endSec(winEnd)
                .text(summaryText)
                .build()
        );
        saved = summaryRepository.save(saved);

        // 6) WebSocket으로 실시간 전송
        Map<String, Object> summaryData = new HashMap<>();
        summaryData.put("id", saved.getId());
        summaryData.put("lectureId", saved.getLectureId());
        summaryData.put("sectionIndex", saved.getSectionIndex());
        summaryData.put("startSec", saved.getStartSec());
        summaryData.put("endSec", saved.getEndSec());
        summaryData.put("text", saved.getText());
        //streamGateway.sendSummary(lectureId, summaryData);

        // 7) AI 서버로 RAG 업서트 (비동기)
        ragClient.upsertSummary(lectureId, saved.getId(), sectionIndex, summaryText);

        // 8) QnA 및 추천 자료 생성 요청 (비동기)
        ragClient.requestQnaGeneration(lectureId, saved.getId(), sectionIndex);
        ragClient.requestResourceRecommendation(lectureId, saved.getId(), sectionIndex);

        return saved;
    }
}

