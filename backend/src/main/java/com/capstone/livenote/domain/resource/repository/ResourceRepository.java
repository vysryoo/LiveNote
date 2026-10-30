package com.capstone.livenote.domain.resource.repository;

import com.capstone.livenote.domain.resource.entity.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ResourceRepository extends JpaRepository<Resource, Long> {
    Page<Resource> findByLectureId(Long lectureId, Pageable pageable);
    List<Resource> findByLectureIdAndSectionIndexOrderByIdAsc(Long lectureId, Integer sectionIndex);

    List<Resource> findByLectureIdAndSectionIndexBetweenOrderByIdAsc(Long lectureId, Integer start, Integer end);

    boolean existsByLectureIdAndSectionIndexAndCardId(Long lectureId, Integer sectionIndex, String cardId);

    boolean existsByIdAndLectureId(Long id, Long lectureId);
}
