package com.capstone.livenote.domain.qna.service;

import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class QnaService {

    private final QnaRepository repo;

    public List<Qna> byLecture(Long lectureId) {
        return repo.findByLectureIdOrderByIdAsc(lectureId);
    }

    public List<Qna> byLectureAndSection(Long lectureId, Integer sectionIndex) {
        return repo.findByLectureIdAndSectionIndexOrderByIdAsc(lectureId, sectionIndex);
    }

}