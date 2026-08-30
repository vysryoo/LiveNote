package com.capstone.livenote.domain.bookmark.repository;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import org.hibernate.tool.schema.TargetType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {

    // 1. 강의 + 섹션 필터링
    List<Bookmark> findByUserIdAndLectureIdAndSectionIndex(Long userId, Long lectureId, Integer sectionIndex);

    // 2. 강의 전체 조회
    List<Bookmark> findByUserIdAndLectureId(Long userId, Long lectureId);

    // 3. 중복 체크
    boolean existsByUserIdAndTargetTypeAndTargetId(Long userId, Bookmark.TargetType targetType, Long targetId);

    // 4. 페이징 지원
    Slice<Bookmark> findByUserIdAndLectureId(Long userId, Long lectureId, Pageable pageable);

    Optional<Bookmark> findByIdAndUserId(Long id, Long userId);
}
