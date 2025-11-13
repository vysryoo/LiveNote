package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;


@Service
@RequiredArgsConstructor
public class SummaryService {

    private final SummaryRepository summaryRepository;
    private final TranscriptRepository transcriptRepository;

    @Transactional(readOnly = true)
    public List<Summary> findSince(Long lectureId, Integer sinceSection) {
        if (sinceSection == null) return summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
        return summaryRepository.findByLectureIdAndSectionIndexGreaterThanOrderBySectionIndexAsc(lectureId, sinceSection);
    }

    // 30초 윈도우 [startSec, endSec) 기반 요약을 생성/업서트
    @Transactional
    public Summary summarizeWindow(Long lectureId, int startSec, int endSec) {
        int sectionIndex = startSec / 30;

        // 1) 윈도우 내 전사 모으기
        var trs = transcriptRepository.findByLectureIdAndStartSecBetweenOrderByStartSecAsc(
                lectureId, startSec, Math.max(startSec, endSec - 1));
        if (trs.isEmpty()) return summaryRepository
                .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                .orElseGet(() -> null);

        int winStart = trs.stream().mapToInt(Transcript::getStartSec).min().orElse(startSec);
        int winEnd   = trs.stream().mapToInt(Transcript::getEndSec).max().orElse(endSec);
        String raw   = String.join(" ", trs.stream().map(Transcript::getText).toList());

        // 2) 요약 생성
        String summaryText = summarizeLocally(raw, 700); // 예: 700자 가드

        // 3) 업서트
        var existing = summaryRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
        Summary saved = existing.map(s -> {
            s.setStartSec(Math.min(s.getStartSec(), winStart));
            s.setEndSec(Math.max(s.getEndSec(), winEnd));
            s.setText(summaryText); // 최신 요약으로 갱신 (또는 축적 방식 선택)
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

        // 4) (선택) 요약 저장 후 AI 서버에 자료추천/QnA 생성 요청 트리거
        // aiClient.requestResourcesAndQna(saved.getId(), lectureId, sectionIndex);

        return saved;
    }

    private String summarizeLocally(String text, int maxLen) {
        if (text == null) return "";
        text = text.trim().replaceAll("\\s+", " ");
        if (text.length() <= maxLen) return text;
        return text.substring(0, maxLen) + " …";
    }
}
