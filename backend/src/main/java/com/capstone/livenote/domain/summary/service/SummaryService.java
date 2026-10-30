package com.capstone.livenote.domain.summary.service;

import com.capstone.livenote.application.ai.dto.SummaryCallbackDto;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;
import java.util.Optional;

import static com.capstone.livenote.application.ai.service.SectionAggregationService.SECTION_SEC;


@Service
@RequiredArgsConstructor
public class SummaryService {

    private final SummaryRepository summaryRepository;

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
        return summaryRepository.findByLectureIdAndSectionIndexLessThanAndPhaseOrderBySectionIndexDesc(
                lectureId,
                sectionIndex,
                SummaryPhase.FINAL,
                pageable
        );
    }

    // 해당 섹션의 요약이 DB에 존재하는지 확인
    @Transactional(noRollbackFor = DataIntegrityViolationException.class)
    public Summary upsertFromCallback(SummaryCallbackDto dto) {
        int startSec = dto.getStartSec() != null ? dto.getStartSec() : dto.getSectionIndex() * SECTION_SEC;
        int endSec = dto.getEndSec() != null ? dto.getEndSec() : startSec + SECTION_SEC;
        SummaryPhase phase = SummaryPhase.from(dto.getPhase());

        // 1. 조회 시도
        Optional<Summary> existingOpt = summaryRepository.findByLectureIdAndSectionIndex(
                dto.getLectureId(), dto.getSectionIndex());

        if (existingOpt.isPresent()) {
            Summary existing = existingOpt.get();
            existing.setText(dto.getText());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            existing.setPhase(phase);
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
                            .phase(phase)
                            .build()
            );
        } catch (DataIntegrityViolationException e) {
            Summary existing = summaryRepository.findByLectureIdAndSectionIndex(
                            dto.getLectureId(), dto.getSectionIndex())
                    .orElseThrow(() -> new IllegalStateException("Summary duplicate error but not found", e));

            existing.setText(dto.getText());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            existing.setPhase(phase);
            return existing;
        }
    }
}
