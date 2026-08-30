package com.capstone.livenote.domain.summary.repository;

import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SummaryRepository extends JpaRepository<Summary, Long> {

    Optional<Summary> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);

    List<Summary> findByLectureIdOrderBySectionIndexAsc(Long lectureId);

    List<Summary> findByLectureIdAndSectionIndexGreaterThanOrderBySectionIndexAsc(
            Long lectureId, Integer sinceSection);

    List<Summary> findByLectureIdAndSectionIndexLessThanOrderBySectionIndexDesc(
            Long lectureId,
            Integer sectionIndex,
            org.springframework.data.domain.Pageable pageable
    );

    List<Summary> findByLectureIdAndSectionIndexLessThanAndPhaseOrderBySectionIndexDesc(
            Long lectureId,
            Integer sectionIndex,
            SummaryPhase phase,
            org.springframework.data.domain.Pageable pageable
    );

    boolean existsByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);

}
