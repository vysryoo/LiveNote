package com.capstone.livenote.domain.resource.controller;

import com.capstone.livenote.domain.resource.dto.ResourceRequestDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.global.ApiResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/resources")
public class ResourceController {

    @Autowired
    private ResourceService resourceService;
    @Autowired
    private ResourceRepository resourceRepository;

    // === AI 서버에서 추천자료 콜백 ===
    @PostMapping("/callback")
    public ApiResponse<Void> saveResourceFromAi(@RequestBody ResourceRequestDto dto) {
        Resource r = Resource.builder()
                .lectureId(dto.getLectureId())
                .summaryId(dto.getSummaryId())
                .userId(dto.getUserId())
                .sectionIndex(dto.getSectionIndex())
                .type(Resource.Type.valueOf(dto.getType().toUpperCase()))
                .title(dto.getTitle())
                .text(dto.getText())
                .url(dto.getUrl())
                .thumbnail(dto.getThumbnail())
                .score(dto.getScore())
                .build();

        resourceRepository.save(r);
        return ApiResponse.ok();
    }

    // === 특정 요약(summary) 기준 추천자료 조회 ===
//    @GetMapping
//    public ApiResponse<List<ResourceResponseDto>> getResources(
//            @RequestParam Long summaryId,
//            @RequestParam(required = false) String type
//    ) {
//        var list = resourceService.bySummary(summaryId, type);
//        var dtoList = list.stream()
//                .map(r -> new ResourceResponseDto(
//                        r.getId(),
//                        r.getLectureId(),
//                        r.getSummaryId(),
//                        r.getSectionIndex(),
//                        r.getType().name().toLowerCase(),
//                        r.getTitle(),
//                        r.getUrl(),
//                        r.getThumbnail(),
//                        r.getScore(),
//                        r.getText()
//                ))
//                .toList();
//        return ApiResponse.ok(dtoList);
//    }

    // 요약 기준 자료 조회
    @GetMapping("/api/summaries/{summaryId}/resources")
    public ApiResponse<List<ResourceResponseDto>> bySummary(
            @PathVariable Long summaryId,
            @RequestParam(required = false) String type
    ) {
        var list = resourceService.bySummary(summaryId, type);
        return ApiResponse.ok(
                list.stream()
                        .map(ResourceResponseDto::from)
                        .toList()
        );
    }
}
