package com.capstone.livenote.domain.transcript.controller;

import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/transcripts")
public class TranscriptController {

    private final TranscriptService transcriptService;

    @GetMapping("/{lectureId}/transcripts")
    public ApiResponse<List<TranscriptResponseDto>> transcripts(
            @PathVariable Long lectureId,
            @RequestParam(required = false) Integer sinceSec
    ){
        var list = transcriptService.findSince(lectureId, sinceSec).stream()
                .map(t -> new TranscriptResponseDto(
                        t.getId(),
                        t.getLectureId(),
                        t.getSectionIndex(),
                        t.getStartSec(),
                        t.getEndSec(),
                        t.getText()
                ))
                .toList();
        return ApiResponse.ok(list);
    }

}

