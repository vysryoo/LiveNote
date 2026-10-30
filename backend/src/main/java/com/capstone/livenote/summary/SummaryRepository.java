package com.capstone.livenote.summary;

import org.springframework.data.domain.Pageable;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SummaryRepository extends JpaRepository<Summary, Long> {

    Optional<Summary> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);

    List<Summary> findByLectureIdOrderBySectionIndexAsc(Long lectureId);

    List<Summary> findByLectureIdAndSectionIndexLessThanAndPhaseOrderBySectionIndexDesc(
            Long lectureId,
            Integer sectionIndex,
            SummaryPhase phase,
            Pageable pageable
    );

}
