package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.application.ai.dto.SummaryCallbackDto;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;

import org.springframework.dao.DataIntegrityViolationException;
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

    @Transactional(readOnly = true)
    public boolean existsByLectureAndSection(Long lectureId, Integer sectionIndex) {
        return summaryRepository.existsByLectureIdAndSectionIndex(lectureId, sectionIndex);
    }

    // 해당 섹션의 요약이 DB에 존재하는지 확인
    @Transactional
    public Summary upsertFromCallback(SummaryCallbackDto dto) {
        int startSec = dto.getStartSec() != null ? dto.getStartSec() : dto.getSectionIndex() * 30;
        int endSec = dto.getEndSec() != null ? dto.getEndSec() : startSec + 30;

        // 1. 조회 시도
        Optional<Summary> existingOpt = summaryRepository.findByLectureIdAndSectionIndex(
                dto.getLectureId(), dto.getSectionIndex());

        if (existingOpt.isPresent()) {
            Summary existing = existingOpt.get();
            existing.setText(dto.getText());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            return existing; // Dirty Checking으로 자동 저장
        }

        // 2. 없으면 저장 시도 (동시성 충돌 발생 가능 구간)
        try {
            return summaryRepository.save(
                    Summary.builder()
                            .lectureId(dto.getLectureId())
                            .sectionIndex(dto.getSectionIndex())
                            .startSec(startSec)
                            .endSec(endSec)
                            .text(dto.getText())
                            .build()
            );
        } catch (DataIntegrityViolationException e) {
            Summary existing = summaryRepository.findByLectureIdAndSectionIndex(
                            dto.getLectureId(), dto.getSectionIndex())
                    .orElseThrow(() -> new IllegalStateException("Summary duplicate error but not found", e));

            existing.setText(dto.getText());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            return existing;
        }
    }
}
