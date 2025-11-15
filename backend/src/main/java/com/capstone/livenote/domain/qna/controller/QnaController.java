package com.capstone.livenote.domain.qna.controller;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.global.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/qna")
public class QnaController {

    @Autowired
    private QnaService qnaService;

    // lectureId 기준 QnA 조회
    @GetMapping
    public ApiResponse<List<QnaResponseDto>> getQnaByLecture(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sectionIndex
    ) {
        var list = (sectionIndex == null)
                ? qnaService.byLecture(lectureId)
                : qnaService.byLectureAndSection(lectureId, sectionIndex);

        var response = list.stream()
                .map(q -> new QnaResponseDto(
                        q.getId(),
                        q.getLectureId(),
                        q.getSectionIndex(),
                        q.getType().name().toLowerCase(),
                        q.getQuestion(),
                        q.getAnswer()
                ))
                .toList();
        return ApiResponse.ok(response);
    }
}
