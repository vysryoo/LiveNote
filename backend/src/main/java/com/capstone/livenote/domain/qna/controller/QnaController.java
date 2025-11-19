package com.capstone.livenote.domain.qna.controller;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@Tag(name = "QnA API", description = "QnA 조회 API")
@RestController
@RequestMapping("/api/qna")
@RequiredArgsConstructor
public class QnaController {

    private final QnaService qnaService;

    @Operation(summary = "강의의 QnA 목록을 조회")
    @GetMapping
    public ApiResponse<List<QnaResponseDto>> getQnaList(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sectionIndex
    ) {
        var list =
                (sectionIndex == null)
                        ? qnaService.byLecture(lectureId)
                        : qnaService.byLectureAndSection(lectureId, sectionIndex);

        var dtoList = list.stream()
                .map(QnaResponseDto::from)
                .toList();

        return ApiResponse.ok(dtoList);
    }
}
