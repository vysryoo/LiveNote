package com.livenote.repository;

import com.livenote.entity.Summary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface SummaryRepository extends JpaRepository<Summary, Long> {
    List<Summary> findByLectureIdOrderBySectionIndexAsc(Long lectureId);
    
    @Query("SELECT s FROM Summary s WHERE s.lectureId = :lectureId AND s.sectionIndex >= :sinceSection ORDER BY s.sectionIndex ASC")
    List<Summary> findByLectureIdAndSinceSection(@Param("lectureId") Long lectureId, @Param("sinceSection") Integer sinceSection);
}

