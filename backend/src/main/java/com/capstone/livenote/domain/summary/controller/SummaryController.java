package com.capstone.livenote.domain.summary.controller;

import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Summary API", description = "강의 요약(Summary)을 조회하는 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/summaries")
public class SummaryController {
    private final ResourceService resourceService;

    private final SummaryService summaryService;

    @Operation(summary = "요약 목록 조회 ")
    @GetMapping
    public ApiResponse<List<SummaryResponseDto>> getSummaries(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sinceSection
    ) {

        Integer sinceChunk = sinceSection;

        var list = summaryService.findSince(lectureId, sinceChunk)
                .stream()
                .map(SummaryResponseDto::from)
                .toList();

        return ApiResponse.ok(list);
    }


    @GetMapping("/{summaryId}/resources")
    public ApiResponse<List<ResourceResponseDto>> resources(
            @PathVariable Long summaryId,
            @RequestParam(required = false) String type) {

        var list = resourceService.bySummary(summaryId, type);
        return ApiResponse.ok(
                list.stream()
                        .map(ResourceResponseDto::from)
                        .toList()
        );

    }
}
