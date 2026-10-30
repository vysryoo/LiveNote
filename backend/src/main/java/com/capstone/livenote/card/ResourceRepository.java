package com.capstone.livenote.card;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ResourceRepository extends JpaRepository<Resource, Long> {
    List<Resource> findByLectureIdOrderBySectionIndexAscIdAsc(Long lectureId);

    List<Resource> findByLectureIdAndSectionIndexOrderByIdAsc(Long lectureId, Integer sectionIndex);

    List<Resource> findByLectureIdAndSectionIndexBetweenOrderByIdAsc(Long lectureId, Integer start, Integer end);

    boolean existsByLectureIdAndSectionIndexAndCardId(Long lectureId, Integer sectionIndex, String cardId);

    boolean existsByIdAndLectureId(Long id, Long lectureId);
}
