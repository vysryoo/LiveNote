package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ai.service.AiRequestService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;


// 프론트가 백엔드한테 ai 작업 요청하는 REST
@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
@Tag(
        name = "AI 요청 API",
        description = "프론트엔드 → 백엔드로 AI 작업(요약 기반 QnA/자료추천) 요청"
)
public class AiController {

    private final AiRequestService aiRequestService;
    private final RagClient ragClient;

    @Operation(
            summary = "특정 섹션에 대한 QnA 생성 요청"
    )
    @PostMapping("/generate-qna")
    public ApiResponse<Void> generateQna(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        aiRequestService.requestQna(lectureId, sectionIndex);
        return ApiResponse.ok();
    }

    @Operation(
            summary = "특정 섹션에 대한 자료 추천 요청"
    )
    @PostMapping("/generate-resources")
    public ApiResponse<Void> generateResources(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        aiRequestService.requestResources(lectureId, sectionIndex);
        return ApiResponse.ok();
    }

    @Operation(summary = "PDF를 업로드하여 RAG 인덱스에 반영")
    @PostMapping(value = "/pdf-upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<Void> uploadPdf(
            @RequestParam Long lectureId,
            @RequestPart("file") MultipartFile file,
            @RequestPart(value = "metadata", required = false) Map<String, Object> metadata
    ) {
        ragClient.upsertPdf(lectureId, file, metadata);
        return ApiResponse.ok();
    }
}
