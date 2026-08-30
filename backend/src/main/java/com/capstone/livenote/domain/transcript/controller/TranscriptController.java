package com.capstone.livenote.domain.transcript.controller;

import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

//@RestController
//@RequiredArgsConstructor
//@RequestMapping("/api/transcripts")
//public class TranscriptController {
//
//    private final TranscriptService transcriptService;
//
//    @GetMapping("/{lectureId}/transcripts")
//    public ApiResponse<List<TranscriptResponseDto>> transcripts(
//            @PathVariable Long lectureId,
//            @RequestParam(required = false) Integer sinceSec
//    ){
//        var list = transcriptService.findSince(lectureId, sinceSec).stream()
//                .map(t -> new TranscriptResponseDto(
//                        t.getId(),
//                        t.getLectureId(),
//                        t.getSectionIndex(),
//                        t.getStartSec(),
//                        t.getEndSec(),
//                        t.getText()
//                ))
//                .toList();
//        return ApiResponse.ok(list);
//    }
//
//}

@RestController
@RequestMapping("/api/transcripts")
@RequiredArgsConstructor
@Tag(name = "Transcript API", description = "강의 전사(Transcript)를 조회하는 API")
public class TranscriptController {

    private final TranscriptService transcriptService;

    @Operation(summary = "전사 목록 조회")
    @GetMapping
    public ApiResponse<List<TranscriptResponseDto>> getTranscripts(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sinceSection
    ) {
        Integer sinceSec = sinceSection;

        var list = transcriptService.findSince(lectureId, sinceSec)
                .stream()
                .map(TranscriptResponseDto::from)
                .toList();

        return ApiResponse.ok(list);
    }
}

