package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ai.service.QnaCallbackService;
import com.capstone.livenote.application.ai.service.ResourceCallbackService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * AI 서버(FastAPI)의 콜백 전용 컨트롤러
 *
 * AI 서버가 처리한 결과를 백엔드로 전송하는 엔드포인트:
 * - QnA 생성 결과
 * - 추천 자료 검색 결과
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai/callback")
public class AiCallbackController {

    private final QnaCallbackService qnaCallbackService;
    private final ResourceCallbackService resourceCallbackService;

    /**
     * AI 서버가 생성한 QnA 저장
     *
     * POST /api/ai/callback/qna
     */
    @PostMapping("/qna")
    public ApiResponse<Void> saveQna(@RequestBody QnaCallbackDto dto) {
        qnaCallbackService.saveQna(dto);
        return ApiResponse.ok();
    }

    /**
     * AI 서버가 검색한 추천 자료 저장
     *
     * POST /api/ai/callback/resources
     */
    @PostMapping("/resources")
    public ApiResponse<Void> saveResources(@RequestBody ResourceCallbackDto dto) {
        resourceCallbackService.saveResources(dto);
        return ApiResponse.ok();
    }
}