package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.dto.CardStatusDto;
import com.capstone.livenote.application.ai.service.AiGenerateService;
import com.capstone.livenote.application.ai.service.AiRequestService;
import com.capstone.livenote.application.ai.service.AiStreamingService;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

@RestController
@RequestMapping("/api") // 명세에 따라 경로 조정 (/api/ai/... 와 /api/cards-status 등이 섞여있음)
@RequiredArgsConstructor
@Tag(name = "AI & Cards API", description = "요약 생성, 카드 상태 조회, 스트리밍")
@Slf4j
public class AiController {

    private final AiGenerateService aiGenerateService;
    private final AiStreamingService aiStreamingService;
    private final AiRequestService aiRequestService;
    private final QnaService qnaService;
    private final ResourceService resourceService;

    // 1. 요약 생성 (Req #1, #2)
//    @Operation(summary = "요약 생성 (15초 Partial / 30초 Final)")
//    @PostMapping("/ai/generate-summary")
//    public ApiResponse<Map<String, Object>> generateSummary(
//            @RequestParam Long lectureId,
//            @RequestParam Integer sectionIndex,
//            @RequestParam String phase
//    ) {
//        try {
//            SummaryResponseDto summary = aiGenerateService.generateSummary(lectureId, sectionIndex, phase);
//            return ApiResponse.ok(Map.of(
//                    "success", true,
//                    "summary", summary,
//                    "sectionIndex", sectionIndex
//            ));
//        } catch (Exception e) {
//            log.error("Summary generation failed", e);
//            return ApiResponse.ok(Map.of("success", false, "error", e.getMessage()));
//        }
//    }

    @PostMapping("/ai/generate-summary")
    public ApiResponse<Map<String, Object>> generateSummary(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        aiGenerateService.generateSummary(lectureId, sectionIndex, "FINAL");
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
        // QnA 조회 및 매핑
        AtomicInteger qIndex = new AtomicInteger(0);
        var qnaList = qnaService.byLectureAndSection(lectureId, sectionIndex).stream()
                .map(q -> CardStatusDto.CardItem.builder()
                        .cardId("qna_" + lectureId + "_" + sectionIndex + "_" + qIndex.getAndIncrement())
                        .cardIndex(qIndex.get() - 1)
                        .type("qna")
                        .isComplete(true)
                        .data(q)
                        .build())
                .toList();

        // Resource 조회 및 매핑
        AtomicInteger rIndex = new AtomicInteger(0);
        var resList = resourceService.findBySectionRange(lectureId, sectionIndex, sectionIndex).stream()
                .map(r -> CardStatusDto.CardItem.builder()
                        .cardId("res_" + lectureId + "_" + sectionIndex + "_" + rIndex.getAndIncrement())
                        .cardIndex(rIndex.get() - 1)
                        .type("resource")
                        .isComplete(true)
                        .data(r)
                        .build())
                .toList();

        return ApiResponse.ok(new CardStatusDto(qnaList, resList));
    }

    // 3. QnA 스트리밍 (Req #4-1)
    @Operation(summary = "QnA 확장 카드 스트리밍 시작")
    @PostMapping("/start-qna-stream")
    public ApiResponse<Map<String, Object>> startQnaStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String qnaType
    ) {
        String cardId = "qna_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        // 비동기 스트리밍 시작
        aiStreamingService.startQnaStreaming(lectureId, sectionIndex, cardId, qnaType);

        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "qna"));
    }

    // 4. Resource 스트리밍 (Req #4-2)
    @Operation(summary = "Resource 확장 카드 스트리밍 시작")
    @PostMapping("/start-resources-stream")
    public ApiResponse<Map<String, Object>> startResourceStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String resourceType
    ) {
        String cardId = "res_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        // 비동기 스트리밍 시작
        aiStreamingService.startResourceStreaming(lectureId, sectionIndex, cardId, resourceType);

        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "resource_stream"));
    }
}
