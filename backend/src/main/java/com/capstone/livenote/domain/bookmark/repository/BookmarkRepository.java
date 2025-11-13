package com.capstone.livenote.domain.bookmark.repository;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import org.hibernate.tool.schema.TargetType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {
    Slice<Bookmark> findByUserIdAndLectureId(Long userId, Long lectureId, Pageable pageable);

    Slice<Bookmark> findByUserIdAndLectureIdAndSectionIndex(
            Long userId, Long lectureId, Integer sectionIndex, Pageable pageable);

//    Optional<Bookmark> findByUserIdAndLectureIdAndSectionIndexAndTargetTypeAndTargetId(
//            Long userId, Long lectureId, Integer sectionIndex, TargetType targetType, Long targetId);
}

