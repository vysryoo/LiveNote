package com.livenote.controller;

import com.livenote.dto.CardStatusDto;
import com.livenote.entity.Lecture;
import com.livenote.entity.QnA;
import com.livenote.entity.Resource;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.QnARepository;
import com.livenote.repository.ResourceRepository;
import com.livenote.service.LectureService;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class CardsStatusController {
    private final QnARepository qnARepository;
    private final ResourceRepository resourceRepository;
    private final LectureRepository lectureRepository;
    private final LectureService lectureService;

    @GetMapping("/cards-status")
    public ResponseEntity<Map<String, Object>> getCardsStatus(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 이미 완료된 QnA 카드들
            List<QnA> completedQnAs = qnARepository
                    .findByLectureIdAndSectionIndex(lectureId, sectionIndex);

            // 이미 완료된 Resource 카드들
            List<Resource> completedResources = resourceRepository
                    .findByLectureIdAndSectionIndex(lectureId, sectionIndex);

            List<CardStatusDto> qnaCards = new ArrayList<>();
            List<CardStatusDto> resourceCards = new ArrayList<>();

            // 완료된 QnA 카드들 (모두 반환 - 제한 없음)
            for (int i = 0; i < completedQnAs.size(); i++) {
                QnA qna = completedQnAs.get(i);
                qnaCards.add(CardStatusDto.builder()
                        .cardId(String.format("qna_%d_%d_%d", lectureId, sectionIndex, i))
                        .cardIndex(i)
                        .type("qna")
                        .isComplete(true)
                        .data(lectureService.toQnADto(qna))
                        .build());
            }

            // 완료된 Resource 카드들 (모두 반환 - 제한 없음)
            for (int i = 0; i < completedResources.size(); i++) {
                Resource resource = completedResources.get(i);
                resourceCards.add(CardStatusDto.builder()
                        .cardId(String.format("resource_%d_%d_%d", lectureId, sectionIndex, i))
                        .cardIndex(i)
                        .type("resource")
                        .isComplete(true)
                        .data(lectureService.toResourceDto(resource))
                        .build());
            }

            Map<String, Object> response = new HashMap<>();
            response.put("qnaCards", qnaCards);
            response.put("resourceCards", resourceCards);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("카드 상태 조회 실패: lectureId={}, sectionIndex={}", lectureId, sectionIndex, e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }
}

