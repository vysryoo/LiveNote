package com.capstone.livenote.domain.summary.controller;

import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/summaries")
public class SummaryController {
    private final ResourceService resourceService;

    private final SummaryService summaryService;

    @GetMapping("/{lectureId}/summaries")
    public ApiResponse<List<SummaryResponseDto>> summaries(
            @PathVariable Long lectureId,
            @RequestParam(required = false) Integer sinceSection // sinceChunk → sinceSection
    ){
        var list = summaryService.findSince(lectureId, sinceSection).stream()
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


    @GetMapping("/{summaryId}/resources")
    public ApiResponse<List<ResourceResponseDto>> resources(
            @PathVariable Long summaryId,
            @RequestParam(required = false) String type) {

        var list = resourceService.bySummary(summaryId, type).stream()
                .map(r -> new ResourceResponseDto(
                        r.getId(),
                        r.getLectureId(),
                        r.getSummaryId(),
                        r.getSectionIndex(),
                        r.getType().name().toLowerCase(),
                        r.getTitle(),
                        r.getUrl(),
                        r.getThumbnail(),
                        r.getScore()
                ))
                .toList();
        return ApiResponse.ok(list);
    }


}
