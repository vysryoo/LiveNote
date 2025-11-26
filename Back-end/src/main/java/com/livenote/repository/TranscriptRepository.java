package com.livenote.repository;

import com.livenote.entity.Transcript;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TranscriptRepository extends JpaRepository<Transcript, Long> {
    List<Transcript> findByLectureIdOrderBySectionIndexAsc(Long lectureId);
    
    @Query("SELECT t FROM Transcript t WHERE t.lectureId = :lectureId AND t.sectionIndex >= :sinceSection ORDER BY t.sectionIndex ASC")
    List<Transcript> findByLectureIdAndSinceSection(@Param("lectureId") Long lectureId, @Param("sinceSection") Integer sinceSection);
    
    List<Transcript> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);
}

