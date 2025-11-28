package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;

import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;
import java.util.Optional;


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

        Summary summary = summaryRepository
                .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                .orElse(null);

        if (summary == null) {
            // 없으면 새로 생성
            summary = Summary.builder()
                    .lectureId(lectureId)
                    .sectionIndex(sectionIndex)
                    .startSec(startSec)
                    .endSec(endSec)
                    .text(text)
                    .build();
        } else {
            // 있으면 덮어쓰기
            summary.setStartSec(startSec);
            summary.setEndSec(endSec);
            summary.setText(text);
        }
        return summaryRepository.save(summary);

    }

    @Transactional(readOnly = true)
    public Optional<Summary> findByLectureAndSection(Long lectureId, Integer sectionIndex) {
        return summaryRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
    }

    @Transactional(readOnly = true)
    public List<Summary> findPreviousSummaries(Long lectureId, Integer sectionIndex, int limit) {
        if (limit <= 0) {
            return List.of();
        }
        var pageable = org.springframework.data.domain.PageRequest.of(
                0,
                limit,
                org.springframework.data.domain.Sort.by("sectionIndex").descending()
        );
        return summaryRepository.findByLectureIdAndSectionIndexLessThanOrderBySectionIndexDesc(
                lectureId,
                sectionIndex,
                pageable
        );
    }

    // 해당 섹션의 요약이 DB에 존재하는지 확인
    @Transactional(readOnly = true)
    public boolean existsByLectureAndSection(Long lectureId, Integer sectionIndex) {

        return summaryRepository.existsByLectureIdAndSectionIndex(lectureId, sectionIndex);
    }
}
