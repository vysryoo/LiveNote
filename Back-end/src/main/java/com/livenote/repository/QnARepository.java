package com.livenote.repository;

import com.livenote.entity.QnA;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface QnARepository extends JpaRepository<QnA, Long> {
    List<QnA> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);
    List<QnA> findByLectureIdAndSectionIndexAndType(Long lectureId, Integer sectionIndex, QnA.QnAType type);
    List<QnA> findByLectureId(Long lectureId);
}

