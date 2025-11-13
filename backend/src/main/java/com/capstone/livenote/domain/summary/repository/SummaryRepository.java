package com.capstone.livenote.domain.summary.repository;

import com.capstone.livenote.domain.summary.entity.Summary;
import org.springframework.data.domain.Example;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SummaryRepository extends JpaRepository<Summary, Long> {

    Optional<Summary> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);

    List<Summary> findByLectureIdOrderBySectionIndexAsc(Long lectureId);

    List<Summary> findByLectureIdAndSectionIndexGreaterThanOrderBySectionIndexAsc(
            Long lectureId, Integer sinceSection);
}