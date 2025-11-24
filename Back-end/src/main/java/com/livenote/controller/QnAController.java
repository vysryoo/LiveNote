package com.livenote.controller;

import com.livenote.dto.QnADto;
import com.livenote.entity.Lecture;
import com.livenote.entity.QnA;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.QnARepository;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/qna")
@RequiredArgsConstructor
public class QnAController {
    private final QnARepository qnARepository;
    private final LectureRepository lectureRepository;

    @GetMapping
    public ResponseEntity<List<QnADto>> getQnA(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam(required = false) String type) {
        Long userId = SecurityUtil.getCurrentUserId();
        
        Lecture lecture = lectureRepository.findById(lectureId)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        List<QnA> qnaList;
        if (type != null) {
            qnaList = qnARepository.findByLectureIdAndSectionIndexAndType(
                    lectureId, sectionIndex, QnA.QnAType.valueOf(type));
        } else {
            qnaList = qnARepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
        }

        List<QnADto> result = qnaList.stream()
                .map(q -> QnADto.builder()
                        .id(q.getId())
                        .lectureId(q.getLectureId())
                        .sectionIndex(q.getSectionIndex())
                        .type(q.getType().name())
                        .question(q.getQuestion())
                        .answer(q.getAnswer())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }
}

