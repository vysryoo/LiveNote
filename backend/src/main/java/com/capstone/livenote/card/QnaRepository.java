package com.capstone.livenote.card;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface QnaRepository extends JpaRepository<Qna, Long> {
    List<Qna> findByLectureIdAndSectionIndexOrderByIdAsc(Long lectureId, Integer sectionIndex);

    List<Qna> findByLectureIdOrderBySectionIndexAscIdAsc(Long lectureId);

    List<Qna> findByLectureIdAndSectionIndexBetweenOrderBySectionIndexAsc(
            Long lectureId,
            Integer start,
            Integer end
    );

    boolean existsByIdAndLectureId(Long id, Long lectureId);
}
