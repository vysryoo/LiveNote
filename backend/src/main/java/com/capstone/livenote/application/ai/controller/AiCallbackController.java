package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ai.dto.SummaryCallbackDto;
import com.capstone.livenote.application.ai.service.QnaCallbackService;
import com.capstone.livenote.application.ai.service.ResourceCallbackService;
import com.capstone.livenote.application.ai.service.SummaryCallbackService;
import com.capstone.livenote.global.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import lombok.extern.slf4j.Slf4j;


// AI 쪽에서 백엔드로 결과 보내기
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai/callback")
@Tag(
        name = "AI 콜백 API",
        description = "AI 서버가 백엔드로 QnA / 자료추천 결과를 전달"
)
@Slf4j
public class AiCallbackController {

    private final QnaCallbackService qnaCallbackService;
    private final ResourceCallbackService resourceCallbackService;
    private final SummaryCallbackService summaryCallbackService;
    private final ObjectMapper objectMapper;

    @Operation(
            summary = "AI 서버가 결과를 백엔드에 전달"
    )
    @PostMapping
    public ApiResponse<Void> handleCallback(
            @RequestParam String type,
            @RequestBody Map<String, Object> payload
    ) {
        log.info("AI callback received type={}, keys={}", type, payload.keySet());
        switch (type) {

            case "qna" -> {
                QnaCallbackDto dto = new ObjectMapper().convertValue(payload, QnaCallbackDto.class);
                qnaCallbackService.handleQnaCallback(dto);
            }

            case "resources" -> {
                ResourceCallbackDto dto = new ObjectMapper().convertValue(payload, ResourceCallbackDto.class);
                resourceCallbackService.handleResourceCallback(dto);
            }

            case "summary" -> {
                SummaryCallbackDto dto = objectMapper.convertValue(payload, SummaryCallbackDto.class);
                summaryCallbackService.handleSummaryCallback(dto);
            }

            default -> throw new IllegalArgumentException("Unsupported callback type: " + type);
        }

        return ApiResponse.ok();
    }
}
