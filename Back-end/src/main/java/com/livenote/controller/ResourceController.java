package com.livenote.controller;

import com.livenote.dto.ResourceDto;
import com.livenote.entity.Lecture;
import com.livenote.entity.Resource;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.ResourceRepository;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/resources")
@RequiredArgsConstructor
public class ResourceController {
    private final ResourceRepository resourceRepository;
    private final LectureRepository lectureRepository;

    @GetMapping
    public ResponseEntity<List<ResourceDto>> getResources(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam(required = false) String type) {
        Long userId = SecurityUtil.getCurrentUserId();
        
        Lecture lecture = lectureRepository.findById(lectureId)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        List<Resource> resources;
        if (type != null) {
            resources = resourceRepository.findByLectureIdAndSectionIndexAndType(
                    lectureId, sectionIndex, Resource.ResourceType.valueOf(type));
        } else {
            resources = resourceRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex);
        }

        List<ResourceDto> result = resources.stream()
                .map(r -> ResourceDto.builder()
                        .id(r.getId())
                        .lectureId(r.getLectureId())
                        .sectionIndex(r.getSectionIndex())
                        .type(r.getType().name())
                        .title(r.getTitle())
                        .text(r.getText())
                        .url(r.getUrl())
                        .thumbnail(r.getThumbnail())
                        .score(r.getScore())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }
}

