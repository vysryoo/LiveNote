package com.capstone.livenote.domain.transcript.repository;

import com.capstone.livenote.domain.transcript.entity.Transcript;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface TranscriptRepository extends JpaRepository<Transcript, Long>
{
    Page<Transcript> findByLectureId(Long lectureId, Pageable pageable);

    List<Transcript> findByLectureIdOrderByStartSecAsc(Long lectureId);

    // 폴링용: sinceSec 초보다 "큰" 전사만 (배타)
    List<Transcript> findByLectureIdAndStartSecGreaterThanOrderByStartSecAsc(
            Long lectureId, Integer sinceSec);

    // 요약 30초 윈도우 수집용
    List<Transcript> findByLectureIdAndStartSecBetweenOrderByStartSecAsc(
            Long lectureId, Integer fromSec, Integer toSec);

    List<Transcript> findByLectureIdAndStartSecGreaterThanEqualOrderByStartSecAsc(
            Long lectureId, Integer sinceSec);

    // 강의의 최대 sectionIndex 조회 (강의 재개 시 이전 섹션 확인용)
    @Query("SELECT MAX(t.sectionIndex) FROM Transcript t WHERE t.lectureId = :lectureId")
    Integer findMaxSectionIndexByLectureId(@Param("lectureId") Long lectureId);

    // 강의의 최대 endSec 조회 (강의 재개 시 시간 계산용)
    @Query("SELECT MAX(t.endSec) FROM Transcript t WHERE t.lectureId = :lectureId")
    Integer findMaxEndSecByLectureId(@Param("lectureId") Long lectureId);


    List<Transcript> findByLectureIdAndSectionIndexOrderByStartSecAsc(Long lectureId, Integer sectionIndex);
}
