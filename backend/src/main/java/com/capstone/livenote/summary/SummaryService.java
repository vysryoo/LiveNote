package com.capstone.livenote.summary;

import com.capstone.livenote.ai.SummaryCallbackDto;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;


import java.util.List;
import java.util.Optional;

import static com.capstone.livenote.recording.SectionAggregationService.SECTION_SEC;


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
        var pageable = PageRequest.of(
                0,
                limit,
                Sort.by("sectionIndex").descending()
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
        int startSec = dto.startSec() != null ? dto.startSec() : dto.sectionIndex() * SECTION_SEC;
        int endSec = dto.endSec() != null ? dto.endSec() : startSec + SECTION_SEC;
        SummaryPhase phase = SummaryPhase.from(dto.phase());

        // 1. 조회 시도
        Optional<Summary> existingOpt = summaryRepository.findByLectureIdAndSectionIndex(
                dto.lectureId(), dto.sectionIndex());

        if (existingOpt.isPresent()) {
            Summary existing = existingOpt.get();
            existing.setText(dto.text());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            existing.setPhase(phase);
            return existing; // Dirty Checking으로 자동 저장
        }

        // 2. 없으면 저장 시도 (동시성 충돌 발생 가능 구간)
        try {
            return summaryRepository.save(
                    Summary.builder()
                            .lectureId(dto.lectureId())
                            .sectionIndex(dto.sectionIndex())
                            .startSec(startSec)
                            .endSec(endSec)
                            .text(dto.text())
                            .phase(phase)
                            .build()
            );
        } catch (DataIntegrityViolationException e) {
            Summary existing = summaryRepository.findByLectureIdAndSectionIndex(
                            dto.lectureId(), dto.sectionIndex())
                    .orElseThrow(() -> new IllegalStateException("Summary duplicate error but not found", e));

            existing.setText(dto.text());
            existing.setStartSec(startSec);
            existing.setEndSec(endSec);
            existing.setPhase(phase);
            return existing;
        }
    }
}
