package com.capstone.livenote.domain.lecture.repository;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import org.springframework.data.domain.Page;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface LectureRepository extends JpaRepository<Lecture, Long> {
    //Page<Lecture> findAllByOrderByCreatedAtDesc(Pageable pageable);

    Page<Lecture> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    @Modifying
    @Query("update Lecture l set l.status=:status where l.id=:id")
    void updateStatus(@Param("id") Long id, @Param("status") Lecture.Status status);
}