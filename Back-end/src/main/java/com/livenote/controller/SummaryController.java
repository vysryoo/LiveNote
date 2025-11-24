package com.livenote.controller;

import com.livenote.dto.SummaryDto;
import com.livenote.entity.Lecture;
import com.livenote.entity.Summary;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.SummaryRepository;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/summaries")
@RequiredArgsConstructor
public class SummaryController {
    private final SummaryRepository summaryRepository;
    private final LectureRepository lectureRepository;

    @GetMapping
    public ResponseEntity<List<SummaryDto>> getSummaries(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sinceSection) {
        Long userId = SecurityUtil.getCurrentUserId();
        
        Lecture lecture = lectureRepository.findById(lectureId)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        List<Summary> summaries;
        if (sinceSection != null) {
            summaries = summaryRepository.findByLectureIdAndSinceSection(lectureId, sinceSection);
        } else {
            summaries = summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
        }

        List<SummaryDto> result = summaries.stream()
                .map(s -> SummaryDto.builder()
                        .id(s.getId())
                        .lectureId(s.getLectureId())
                        .sectionIndex(s.getSectionIndex())
                        .startSec(s.getStartSec())
                        .endSec(s.getEndSec())
                        .text(s.getText())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }
}

