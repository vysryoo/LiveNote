package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ai.dto.CardStatusDto;
import com.capstone.livenote.application.ai.service.AiRequestService;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api") // 명세에 따라 경로 조정 (/api/ai/... 와 /api/cards-status 등이 섞여있음)
@RequiredArgsConstructor
@Tag(name = "AI & Cards API", description = "요약 생성, 카드 상태 조회, 스트리밍")
@Slf4j
public class AiController {

    private final RagClient ragClient;
    private final TranscriptService transcriptService;
    private final AiRequestService aiRequestService;

    // 1. 요약 생성 (수동 트리거)
    @Operation(summary = "수동 요약 생성 요청 (테스트용)")
    @PostMapping("/ai/generate-summary")
    public ApiResponse<Map<String, Object>> generateSummary(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam(defaultValue = "FINAL") String phase
    ) {
        // 1) DB에서 전사 텍스트 조회
        String transcript = transcriptService.getCombinedText(lectureId, sectionIndex);

        if (transcript == null || transcript.isBlank()) {
            return ApiResponse.ok(Map.of("success", false, "message", "전사 텍스트가 없습니다."));
        }

        // 2) AI 서버로 요청 (RagClient 직접 사용)
        int startSec = sectionIndex * 30;
        int endSec = startSec + 30;

        ragClient.requestSummaryGeneration(
                lectureId,
                null, // id는 null (새로 생성하거나 콜백에서 처리)
                sectionIndex,
                startSec,
                endSec,
                phase,
                transcript
        );

        return ApiResponse.ok(Map.of("success", true));
    }

    @PostMapping("/ai/generate-resources")
    public ApiResponse<Map<String, Object>> generateResources(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        aiRequestService.requestResources(lectureId, sectionIndex);
        return ApiResponse.ok(Map.of("success", true));
    }

    @PostMapping("/ai/generate-qna")
    public ApiResponse<Map<String, Object>> generateQna(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        aiRequestService.requestQna(lectureId, sectionIndex);
        return ApiResponse.ok(Map.of("success", true));
    }



    // 2. 카드 상태 조회 (Req #3)
    @Operation(summary = "카드 상태 조회 (요약 카드 클릭 시)")
    @GetMapping("/cards-status")
    public ApiResponse<CardStatusDto> getCardsStatus(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        return ApiResponse.ok(aiRequestService.getCardsStatus(lectureId, sectionIndex));
    }

    // 3. QnA 스트리밍
    @Operation(summary = "QnA 확장 카드 스트리밍 시작")
    @PostMapping("/start-qna-stream")
    public ApiResponse<Map<String, Object>> startQnaStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String qnaType
    ) {
        aiRequestService.requestQnaWithType(lectureId, sectionIndex, qnaType);
        String cardId = "qna_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "qna"));
    }

    // 4. Resource 스트리밍
    @Operation(summary = "Resource 확장 카드 스트리밍 시작")
    @PostMapping("/start-resources-stream")
    public ApiResponse<Map<String, Object>> startResourceStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String resourceType
    ) {
        aiRequestService.requestResourcesWithType(lectureId, sectionIndex, resourceType);
        String cardId = "res_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "resource_stream"));
    }
}
