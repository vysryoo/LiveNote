package com.capstone.livenote.domain.bookmark.repository;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import org.hibernate.tool.schema.TargetType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Slice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {

    // 중복 체크
    boolean existsByUserIdAndTargetTypeAndTargetId(Long userId, Bookmark.TargetType targetType, Long targetId);

    // 페이징 지원
    Slice<Bookmark> findByUserIdAndLectureId(Long userId, Long lectureId, Pageable pageable);

    Optional<Bookmark> findByIdAndUserId(Long id, Long userId);
}
