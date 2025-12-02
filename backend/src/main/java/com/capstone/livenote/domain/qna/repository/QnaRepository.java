package com.capstone.livenote.domain.qna.repository;

import com.capstone.livenote.domain.qna.entity.Qna;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface QnaRepository extends JpaRepository<Qna, Long> {
    Page<Qna> findByLectureId(Long lectureId, Pageable pageable);

    List<Qna> findByLectureIdOrderByIdAsc(Long lectureId);

    List<Qna> findByLectureIdAndSectionIndexOrderByIdAsc(Long lectureId, Integer sectionIndex);

    List<Qna> findByLectureIdOrderBySectionIndexAsc(Long lectureId);

    List<Qna> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);

    List<Qna> findByLectureIdAndSectionIndexBetweenOrderBySectionIndexAsc(
            Long lectureId,
            Integer start,
            Integer end
    );

    boolean existsByLectureIdAndSectionIndexAndCardId(Long lectureId, Integer sectionIndex, String cardId);

    boolean existsByLectureIdAndSectionIndexAndQuestionAndAnswer(Long lectureId, Integer sectionIndex, String question, String answer);
}
