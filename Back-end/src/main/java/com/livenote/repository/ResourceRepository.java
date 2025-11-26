package com.livenote.repository;

import com.livenote.entity.Resource;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ResourceRepository extends JpaRepository<Resource, Long> {
    List<Resource> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);
    List<Resource> findByLectureIdAndSectionIndexAndType(Long lectureId, Integer sectionIndex, Resource.ResourceType type);
    List<Resource> findByLectureId(Long lectureId);
}

