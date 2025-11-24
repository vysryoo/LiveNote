package com.livenote.repository;

import com.livenote.entity.Bookmark;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {
    List<Bookmark> findByLectureIdAndSectionIndex(Long lectureId, Integer sectionIndex);
    List<Bookmark> findByUserIdAndLectureIdAndSectionIndex(Long userId, Long lectureId, Integer sectionIndex);
    List<Bookmark> findByUserIdAndLectureId(Long userId, Long lectureId);
}

