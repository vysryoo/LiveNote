package com.capstone.livenote.domain.transcript.repository;

import com.capstone.livenote.domain.transcript.entity.Transcript;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

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

}
