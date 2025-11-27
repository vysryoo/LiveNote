package com.capstone.livenote.domain.lecture.controller;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.audio.service.AudioIngestService;
import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.dto.LectureResponseDto;
import com.capstone.livenote.domain.lecture.dto.SessionDetailResponse;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;

import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.io.IOException;
import java.util.List;

@Tag(
        name = "Lecture API",
        description = "강의를 생성/조회/종료하고, 이후 전사/요약/자료 추천과 연결되기 위한 기본 강의 관리 API"
)
@RestController
@RequestMapping("/api/lectures")
@RequiredArgsConstructor
public class LectureController {
    private final LectureService lectureService;
    private final AudioIngestService audio;
    private final TranscriptService trQuery;
    private final SummaryService smQuery;
    private final QnaService qnaService;
    private final RagClient ragClient;

    private Long currentUserId(){
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "not authenticated");
        }
        
        String userIdStr = authentication.getName();
        try {
            return Long.parseLong(userIdStr);
        } catch (NumberFormatException e) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "invalid user id");
        }
    }

    // 강의 조회
    @Operation(summary = "현재 사용자의 최근 강의 목록을 조회")
    @GetMapping
    public ApiResponse<List<LectureResponseDto>> list() {
        var list = lectureService.list(currentUserId(), PageRequest.of(0, 20))
                .stream()
                .map(LectureResponseDto::from)
                .toList();
        return ApiResponse.ok(list);
    }

    // 강의 상세 조회
    @Operation(summary = "특정 강의의 상세 정보를 조회")
    @GetMapping("/{lectureId}")
    public ApiResponse<LectureResponseDto> get(@PathVariable Long lectureId){
        var l = lectureService.get(lectureId);
        return ApiResponse.ok(LectureResponseDto.from(l));
    }

    // 강의 상세 정보 조회 (transcripts, summaries, resources, qna, bookmarks 포함)
    @Operation(summary = "강의의 모든 상세 정보 조회 (transcripts, summaries, resources, qna, bookmarks 포함)")
    @GetMapping("/{lectureId}/detail")
    public ApiResponse<SessionDetailResponse> getDetail(@PathVariable Long lectureId){
        var detail = lectureService.getSessionDetail(lectureId);
        return ApiResponse.ok(detail);
    }

    // 강의 생성
    @Operation(summary = "새로운 강의를 생성")
    @PostMapping
    public ApiResponse<LectureResponseDto> create(@RequestBody CreateLectureRequestDto req){
        var l = lectureService.create(currentUserId(), req);
        return ApiResponse.ok(LectureResponseDto.from(l));
    }



    // 오디오 청크 업로드 ( AI 서버용 )
    @Operation(summary = "AI 서버로 전송할 오디오 청크를 업로드")
    @PostMapping(value="/{lectureId}/audio/chunk",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<Void> uploadChunk(
            @PathVariable Long lectureId,
            @RequestPart("file") MultipartFile file,
            @RequestParam int chunkSeq,
            @RequestParam int startSec,
            @RequestParam int endSec
    ) throws IOException {
        audio.uploadChunk(lectureId, chunkSeq, startSec, endSec, file);
        return ApiResponse.ok();
    }

    // 강의 종료
    @Operation(summary = "녹음을 종료하고 강의 상태를 완료로 변경")
    @PostMapping("/{lectureId}/end")
    public ApiResponse<Void> endLecture(@PathVariable Long lectureId) {
        // 1) 강의 상태 COMPLETED
        lectureService.endLecture(lectureId);

        // 2) 오디오 인입 종료 처리
        audio.markComplete(lectureId);

        return ApiResponse.ok();
    }


    // endLecture 이랑 연결되는 것
//    @PostMapping("/{lectureId}/audio/complete")
//    @Deprecated
//    public ApiResponse<Void> complete(@PathVariable Long lectureId){
//        return endLecture(lectureId);
//    }

    @Operation(summary = "특정 강의와 관련 데이터를 삭제")
    @DeleteMapping("/{lectureId}")
    public ApiResponse<Void> delete(@PathVariable Long lectureId){
        lectureService.delete(lectureId);
        return ApiResponse.ok();
    }


    // PDF 업로드 및 RAG 업서트 요청
    @Operation(summary = "강의 PDF 자료 업로드 (RAG 업서트)")
    @PostMapping(value = "/{lectureId}/pdf", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<String> uploadPdf(
            @PathVariable Long lectureId,
            @RequestPart("file") MultipartFile file
    ) {
        // 1. 사용자 권한 검증 (선택 사항이나 권장)
        //Long userId = currentUserId();
        // lectureService.validateOwner(lectureId, userId); // 필요 시 추가

        // 2. AI 서버로 전송하여 RAG 업서트 수행 및 collectionId 획득
        // (RagClient.upsertPdf는 이제 String collectionId를 반환해야 함)
        String collectionId = ragClient.upsertPdf(lectureId, file, null);

        // 3. DB에 collectionId 업데이트
        lectureService.updateCollectionId(lectureId, collectionId);

        return ApiResponse.ok(collectionId);
    }

    // 전사
//    @Operation(summary = "전사 목록 조회 (내부용)", hidden = true)
//    @GetMapping("/{lectureId}/transcripts")
//    public ApiResponse<List<TranscriptResponseDto>> transcripts(
//            @PathVariable Long lectureId,
//            @RequestParam(required = false) Integer sinceSec
//    ){
//        var list = trQuery.findSince(lectureId, sinceSec).stream()
//                .map(TranscriptResponseDto::from)
//                .toList();
//
//        return ApiResponse.ok(list);
//    }

    // 요약
//    @Operation(summary = "강의의 요약 목록을 조회")
//    @GetMapping("/{lectureId}/summaries")
//    public ApiResponse<List<SummaryResponseDto>> summaries(
//            @PathVariable Long lectureId,
//            @RequestParam(required = false) Integer sinceChunk){
//        var list = smQuery.findSince(lectureId, sinceChunk).stream()
//                .map(SummaryResponseDto::from)
//                .toList();
//        return ApiResponse.ok(list);
//    }

    // QnA
//    @Operation(summary = "강의에 대한 QnA 목록을 조회")
//    @GetMapping("/{lectureId}/qna")
//    public ApiResponse<List<QnaResponseDto>> qna(@PathVariable Long lectureId){
//        var list = qnaService.byLecture(lectureId).stream()
//                .map(QnaResponseDto::from)
//                .toList();
//        return ApiResponse.ok(list);
//    }

}
