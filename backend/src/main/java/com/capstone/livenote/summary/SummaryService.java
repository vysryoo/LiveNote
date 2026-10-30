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

/**
 * 섹션 요약의 조회와 최종 요약 저장을 맡는다. 부분 요약은 저장하지 않는다.
 */
@Service
@RequiredArgsConstructor
public class SummaryService {

    private final SummaryRepository summaryRepository;

    /**
     * 섹션의 저장된 요약을 조회한다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @return 요약. 아직 최종 요약이 저장되지 않았으면 비어 있음
     */
    @Transactional(readOnly = true)
    public Optional<Summary> findByLectureAndSection(Long lectureId, Integer sectionIndex) {
        return summaryRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
    }

    /**
     * 현재 섹션보다 앞선 최종 요약을 가까운 섹션부터 조회한다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 현재 섹션 번호
     * @param limit 최대 개수. 0 이하면 빈 목록
     * @return 최종 요약 목록. 섹션 번호가 큰 것부터
     */
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

    /**
     * AI 서버가 보낸 요약을 섹션의 요약으로 저장한다. 이미 있으면 덮어쓴다.
     *
     * 콜백에 시각이 없으면 섹션 번호와 섹션 길이(30초)로 채운다.
     *
     * @param dto 요약 콜백 본문
     * @return 저장한 요약
     * @throws IllegalStateException unique 제약 위반이 났는데 다시 조회해도 요약이 없는 경우
     */
    @Transactional(noRollbackFor = DataIntegrityViolationException.class)
    public Summary upsertFromCallback(SummaryCallbackDto dto) {
        int startSec = dto.startSec() != null ? dto.startSec() : dto.sectionIndex() * SECTION_SEC;
        int endSec = dto.endSec() != null ? dto.endSec() : startSec + SECTION_SEC;
        SummaryPhase phase = SummaryPhase.from(dto.phase());

        Optional<Summary> existingOpt = summaryRepository.findByLectureIdAndSectionIndex(
                dto.lectureId(), dto.sectionIndex());

        if (existingOpt.isPresent()) {
            return overwrite(existingOpt.get(), dto.text(), startSec, endSec, phase);
        }

        // 같은 섹션의 콜백이 동시에 들어와 다른 쪽이 먼저 저장하면 unique 제약 위반이 남
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
            return overwrite(existing, dto.text(), startSec, endSec, phase);
        }
    }

    // 조회한 엔티티의 값만 바꾸면 트랜잭션이 끝날 때 dirty checking으로 저장됨
    private static Summary overwrite(Summary summary, String text, int startSec, int endSec, SummaryPhase phase) {
        summary.setText(text);
        summary.setStartSec(startSec);
        summary.setEndSec(endSec);
        summary.setPhase(phase);
        return summary;
    }
}
