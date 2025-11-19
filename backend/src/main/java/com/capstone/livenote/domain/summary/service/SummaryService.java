package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;

import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;


@Service
@RequiredArgsConstructor
public class SummaryService {

    private final SummaryRepository summaryRepository;

    // 강의 요약 리스트 조회
    @Transactional(readOnly = true)
    public List<Summary> findSince(Long lectureId, Integer sinceSection) {
        if (sinceSection == null) return summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
        return summaryRepository.findByLectureIdAndSectionIndexGreaterThanOrderBySectionIndexAsc(lectureId, sinceSection);
    }

    @Transactional
    public Summary createSectionSummary(Long lectureId,
                                        Integer sectionIndex,
                                        String text) {

        int startSec = sectionIndex * 30;
        int endSec = startSec + 30;

        Summary summary = Summary.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .startSec(startSec)
                .endSec(endSec)
                .text(text)
                .build();

        return summaryRepository.save(summary);
    }
}

