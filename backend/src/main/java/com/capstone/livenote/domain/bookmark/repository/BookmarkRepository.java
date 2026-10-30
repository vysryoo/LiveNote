package com.capstone.livenote.domain.bookmark.repository;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import org.hibernate.tool.schema.TargetType;
import org.springframework.data.domain.Page;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {

    // 중복 체크
    boolean existsByUserIdAndTargetTypeAndTargetId(Long userId, Bookmark.TargetType targetType, Long targetId);

    List<Bookmark> findByUserIdAndLectureIdOrderBySectionIndexAscIdAsc(Long userId, Long lectureId);

    Optional<Bookmark> findByIdAndUserId(Long id, Long userId);
}
