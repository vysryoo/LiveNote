package com.capstone.livenote.domain.resource.controller;

import com.capstone.livenote.domain.resource.dto.ResourceRequestDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Resource API", description = "강의 섹션별 추천 자료를 조회하는 API")
@RestController
@RequestMapping("/api/resources")
public class ResourceController {

    @Autowired
    private ResourceService resourceService;
    @Autowired
    private ResourceRepository resourceRepository;
    @Autowired
    private SummaryRepository summaryRepository;

    // === AI 서버에서 추천자료 콜백 ===
    @PostMapping("/callback")
    public ApiResponse<Void> saveResourceFromAi(@RequestBody ResourceRequestDto dto) {
        Resource r = Resource.builder()
                .lectureId(dto.getLectureId())
                .summaryId(dto.getSummaryId())
                .userId(dto.getUserId())
                .sectionIndex(dto.getSectionIndex())
                .type(Resource.Type.fromString(dto.getType()))
                .title(dto.getTitle())
                .text(dto.getText())
                .url(dto.getUrl())
                .thumbnail(dto.getThumbnail())
                .score(dto.getScore())
                .reason(dto.getReason())
                .detail(dto.getDetail() == null ? null : new com.fasterxml.jackson.databind.ObjectMapper().valueToTree(dto.getDetail()))
                .build();

        resourceRepository.save(r);
        return ApiResponse.ok();
    }

    @Operation(summary = "추천 자료 조회 ")
    @GetMapping
    public ApiResponse<List<ResourceResponseDto>> getResources(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam(required = false) String type
    ) {
        // 1) lectureId + sectionIndex 에 해당하는 Summary 찾기
        Summary summary = summaryRepository
                .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                .orElseThrow(() -> new IllegalArgumentException("요약을 찾을 수 없습니다."));

        // 2) summaryId 기준으로 Resource 조회
        var list = resourceService.bySummary(summary.getId(), type)
                .stream()
                .map(ResourceResponseDto::from)
                .toList();

        return ApiResponse.ok(list);
    }

}
