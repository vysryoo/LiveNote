package com.capstone.livenote.domain.lecture.repository;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import org.springframework.data.domain.Page;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

public interface LectureRepository extends JpaRepository<Lecture, Long> {

    Page<Lecture> findByUserIdOrderByCreatedAtDesc(Long userId, Pageable pageable);

    Optional<Lecture> findByIdAndUserId(Long id, Long userId);
}