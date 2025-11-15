package com.capstone.livenote.domain.lecture.controller;

import com.capstone.livenote.application.audio.service.AudioIngestService;
import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.dto.LectureResponseDto;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

import static java.util.stream.Collectors.toList;

@RestController
@RequestMapping("/api/lectures")
@RequiredArgsConstructor
public class LectureController {
    private final LectureService lectureService;
    private final AudioIngestService audio;
    private final TranscriptService trQuery;
    private final SummaryService smQuery;
    private final ResourceService rsQuery;
    private final QnaService qnaService;

    private Long currentUserId(){ return 1L; } // 임시. 실제는 SecurityContext에서 꺼내기

    // 강의 조회
    @GetMapping
    public ApiResponse<List<LectureResponseDto>> list() {
        var list = lectureService.list(currentUserId(), PageRequest.of(0, 20))
                .stream()
                .map(LectureResponseDto::from)
                .toList();
        return ApiResponse.ok(list);
    }


    // 강의 생성
    @PostMapping
    public ApiResponse<LectureResponseDto> create(@RequestBody CreateLectureRequestDto req){
        var l = lectureService.create(currentUserId(), req);
        return ApiResponse.ok(LectureResponseDto.from(l));
    }

    // 강의 상세 조회
    @GetMapping("/{lectureId}")
    public ApiResponse<LectureResponseDto> get(@PathVariable Long lectureId){
        var l = lectureService.get(lectureId);
        return ApiResponse.ok(LectureResponseDto.from(l));
    }


    // 오디오 청크 업로드
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

    @PostMapping("/{lectureId}/audio/complete")
    public ApiResponse<Void> complete(@PathVariable Long lectureId){
        lectureService.startProcessing(lectureId);
        audio.markComplete(lectureId);
        return ApiResponse.ok();
    }

    @DeleteMapping("/{lectureId}")
    public ApiResponse<Void> delete(@PathVariable Long lectureId){
        lectureService.delete(lectureId);
        return ApiResponse.ok();
    }


    // 전사
    @GetMapping("/{lectureId}/transcripts")
    public ApiResponse<List<TranscriptResponseDto>> transcripts(
            @PathVariable Long lectureId,
            @RequestParam(required = false) Integer sinceSec){
        var list = trQuery.findSince(lectureId, sinceSec).stream()
                .map(t -> new TranscriptResponseDto(
                        t.getId(),
                        t.getLectureId(),       // FK 필드
                        t.getSectionIndex(),
                        t.getStartSec(),
                        t.getEndSec(),
                        t.getText()
                ))
                .toList();
        return ApiResponse.ok(list);
    }

    // 요약
    @GetMapping("/{lectureId}/summaries")
    public ApiResponse<List<SummaryResponseDto>> summaries(
            @PathVariable Long lectureId,
            @RequestParam(required = false) Integer sinceChunk){
        var list = smQuery.findSince(lectureId, sinceChunk).stream()
                .map(s -> new SummaryResponseDto(
                        s.getId(),
                        s.getLectureId(),
                        s.getSectionIndex(),
                        s.getStartSec(),
                        s.getEndSec(),
                        s.getText()
                ))
                .toList();
        return ApiResponse.ok(list);
    }

    // QnA
// === QnA ===
    @GetMapping("/{lectureId}/qna")
    public ApiResponse<List<QnaResponseDto>> qna(@PathVariable Long lectureId){
        var list = qnaService.byLecture(lectureId).stream()
                .map(QnaResponseDto::from)
                .toList();
        return ApiResponse.ok(list);
    }

}

