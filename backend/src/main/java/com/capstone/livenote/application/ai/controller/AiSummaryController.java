//package com.capstone.livenote.application.ai.controller;
//
//import com.capstone.livenote.domain.lecture.service.LectureService;
//import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
//import com.capstone.livenote.global.ApiResponse;
//import io.swagger.v3.oas.annotations.Operation;
//import io.swagger.v3.oas.annotations.tags.Tag;
//import lombok.RequiredArgsConstructor;
//import org.springframework.web.bind.annotation.PostMapping;
//import org.springframework.web.bind.annotation.RequestMapping;
//import org.springframework.web.bind.annotation.RequestParam;
//import org.springframework.web.bind.annotation.RestController;
//
///**
// * 프론트가 수동 요약 생성 API를 호출할 때 404/500을 피하기 위한 최소 응답 컨트롤러.
// * 실제 요약은 실시간 STT/섹션 집계에서 처리되므로 여기서는 더미 응답을 내려준다.
// */
//@RestController
//@RequestMapping("/api/ai")
//@RequiredArgsConstructor
//@Tag(name = "AI Summary Stub", description = "수동 요약 요청에 대한 더미 응답")
//public class AiSummaryController {
//
//    private final LectureService lectureService;
//
//    @Operation(summary = "수동 요약 요청 (더미 응답)")
//    @PostMapping("/generate-summary")
//    public ApiResponse<SummaryGenerateResponse> generateSummary(
//            @RequestParam Long lectureId,
//            @RequestParam Integer sectionIndex,
//            @RequestParam(required = false, defaultValue = "partial") String phase
//    ) {
//        // 강의 존재 확인만 수행
//        lectureService.get(lectureId);
//
//        int startSec = sectionIndex * 30;
//        int endSec = startSec + 30;
//        SummaryResponseDto summary = SummaryResponseDto.builder()
//                .id(null)
//                .lectureId(lectureId)
//                .sectionIndex(sectionIndex)
//                .startSec(startSec)
//                .endSec(endSec)
//                .text("(서버에서 수동 요약 생성은 지원하지 않습니다. 실시간 요약/콜백을 사용하세요.)")
//                .phase("final".equalsIgnoreCase(phase) ? SummaryResponseDto.Phase.FINAL : SummaryResponseDto.Phase.PARTIAL)
//                .build();
//
//        SummaryGenerateResponse resp = new SummaryGenerateResponse(true, summary, sectionIndex, null);
//        return ApiResponse.ok(resp);
//    }
//
//    public record SummaryGenerateResponse(boolean success,
//                                          SummaryResponseDto summary,
//                                          Integer sectionIndex,
//                                          String error) { }
//}
