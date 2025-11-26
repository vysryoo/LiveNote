package com.livenote.controller;

import com.livenote.dto.TranscriptDto;
import com.livenote.entity.Lecture;
import com.livenote.entity.Transcript;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.TranscriptRepository;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/transcripts")
@RequiredArgsConstructor
public class TranscriptController {
    private final TranscriptRepository transcriptRepository;
    private final LectureRepository lectureRepository;

    @GetMapping
    public ResponseEntity<List<TranscriptDto>> getTranscripts(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sinceSection) {
        Long userId = SecurityUtil.getCurrentUserId();
        
        Lecture lecture = lectureRepository.findById(lectureId)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        List<Transcript> transcripts;
        if (sinceSection != null) {
            transcripts = transcriptRepository.findByLectureIdAndSinceSection(lectureId, sinceSection);
        } else {
            transcripts = transcriptRepository.findByLectureIdOrderBySectionIndexAsc(lectureId);
        }

        List<TranscriptDto> result = transcripts.stream()
                .map(t -> TranscriptDto.builder()
                        .id(t.getId())
                        .lectureId(t.getLectureId())
                        .sectionIndex(t.getSectionIndex())
                        .startSec(t.getStartSec())
                        .endSec(t.getEndSec())
                        .text(t.getText())
                        .build())
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }
}

