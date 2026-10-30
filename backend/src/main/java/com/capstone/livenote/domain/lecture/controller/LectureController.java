package com.capstone.livenote.domain.lecture.controller;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.dto.EndLectureRequest;
import com.capstone.livenote.domain.lecture.dto.LecturePageDto;
import com.capstone.livenote.domain.lecture.dto.LectureResponseDto;
import com.capstone.livenote.domain.lecture.dto.SessionDetailResponse;
import com.capstone.livenote.domain.lecture.dto.UpdateLectureTitleRequest;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;

import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Tag(
        name = "Lecture API",
        description = "강의를 생성/조회/종료하고, 이후 전사/요약/자료 추천과 연결되기 위한 기본 강의 관리 API"
)
@RestController
@RequestMapping("/api/lectures")
@RequiredArgsConstructor
public class LectureController {
    private static final int MAX_PAGE_SIZE = 100;

    private final LectureService lectureService;
    private final RagClient ragClient;

    // 강의 조회
    @Operation(summary = "현재 사용자의 강의 목록을 최신순으로 페이지 단위 조회")
    @GetMapping
    public ApiResponse<LecturePageDto> list(
            @AuthenticationPrincipal Long userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        // 한 번에 너무 많이 요청하지 못하도록 페이지 크기를 제한
        int safeSize = Math.min(Math.max(size, 1), MAX_PAGE_SIZE);
        var result = lectureService.list(userId, PageRequest.of(Math.max(page, 0), safeSize));
        var items = result.stream().map(LectureResponseDto::from).toList();
        return ApiResponse.ok(new LecturePageDto(items, result.getTotalElements(), result.hasNext()));
    }

    // 강의 상세 정보 조회 (transcripts, summaries, resources, qna, bookmarks 포함)
    @Operation(summary = "강의의 모든 상세 정보 조회 (transcripts, summaries, resources, qna, bookmarks 포함)")
    @GetMapping("/{lectureId}/detail")
    public ApiResponse<SessionDetailResponse> getDetail(@AuthenticationPrincipal Long userId,
                                                        @PathVariable Long lectureId){
        lectureService.getOwned(lectureId, userId);
        var detail = lectureService.getSessionDetail(lectureId);
        return ApiResponse.ok(detail);
    }

    // 강의 생성
    @Operation(summary = "새로운 강의를 생성")
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public ApiResponse<LectureResponseDto> create(@AuthenticationPrincipal Long userId,
                                                  @RequestBody CreateLectureRequestDto req){
        var l = lectureService.create(userId, req);
        return ApiResponse.ok(LectureResponseDto.from(l));
    }

    @Operation(summary = "새로운 강의를 생성 (PDF 업로드 포함)")
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<LectureResponseDto> createWithPdf(
            @AuthenticationPrincipal Long userId,
            @RequestPart("title") String title,
            @RequestPart("subject") String subject,
            @RequestPart("sttLanguage") String sttLanguage,
            @RequestPart(value = "files", required = false) List<MultipartFile> files
    ) {
        if (files == null || files.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "PDF 파일이 필요합니다.");
        }
        MultipartFile pdf = files.get(0);
        if (pdf == null || pdf.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "PDF 파일이 비어있습니다.");
        }
        String contentType = pdf.getContentType();
        if (contentType == null || !contentType.equalsIgnoreCase("application/pdf")) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "PDF 파일만 업로드할 수 있습니다.");
        }

        var req = new CreateLectureRequestDto(title, subject, sttLanguage);
        var lecture = lectureService.create(userId, req);

        // RAG 업서트 수행
        String collectionId = ragClient.upsertPdf(lecture.getId(), pdf, null);
        lectureService.updateCollectionId(lecture.getId(), collectionId);

        return ApiResponse.ok(LectureResponseDto.from(lecture));
    }


    // 강의 종료
    @Operation(summary = "녹음을 종료하고 강의 상태를 완료로 변경")
    @PostMapping("/{lectureId}/end")
    public ApiResponse<LectureResponseDto> endLecture(
            @AuthenticationPrincipal Long userId,
            @PathVariable Long lectureId,
            @RequestBody(required = false) EndLectureRequest request
    ) {
        lectureService.getOwned(lectureId, userId);
        var lecture = lectureService.endLecture(lectureId, request == null ? null : request.title());
        return ApiResponse.ok(LectureResponseDto.from(lecture));
    }

    @Operation(summary = "특정 강의와 관련 데이터를 삭제")
    @DeleteMapping("/{lectureId}")
    public ApiResponse<Void> delete(@AuthenticationPrincipal Long userId, @PathVariable Long lectureId){
        lectureService.getOwned(lectureId, userId);
        lectureService.delete(lectureId);
        return ApiResponse.ok();
    }

    @Operation(summary = "강의 제목 수정")
    @PatchMapping("/{lectureId}/title")
    public ApiResponse<LectureResponseDto> updateTitle(
            @AuthenticationPrincipal Long userId,
            @PathVariable Long lectureId,
            @RequestBody UpdateLectureTitleRequest req
    ) {
        lectureService.getOwned(lectureId, userId);
        var updated = lectureService.updateLectureTitle(lectureId, req.getTitle());
        return ApiResponse.ok(LectureResponseDto.from(updated));
    }

}
