package com.capstone.livenote.lecture;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {

    // 중복 체크
    boolean existsByUserIdAndTargetTypeAndTargetId(Long userId, Bookmark.TargetType targetType, Long targetId);

    List<Bookmark> findByUserIdAndLectureIdOrderBySectionIndexAscIdAsc(Long userId, Long lectureId);

    Optional<Bookmark> findByIdAndUserId(Long id, Long userId);
}
