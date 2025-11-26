package com.livenote.controller;

import com.livenote.entity.Lecture;
import com.livenote.repository.LectureRepository;
import com.livenote.service.AIStreamingService;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class StreamingController {
    private final AIStreamingService aiStreamingService;
    private final LectureRepository lectureRepository;

    /**
     * QnA 스트리밍 시작
     * @param qnaType 선택적 파라미터: 타입이 제공되면 해당 타입의 QnA를 생성 (concept, application, advanced, comparison)
     */
    @PostMapping("/start-qna-stream")
    public ResponseEntity<Map<String, Object>> startQnAStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam(required = false) String qnaType) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 고유 카드 ID 생성
            String cardId = String.format("qna_%d_%d_%d", lectureId, sectionIndex, cardIndex);

            // 비동기로 스트리밍 시작
            aiStreamingService.streamQnA(lectureId, sectionIndex, cardIndex, cardId, qnaType);

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("cardId", cardId);
            response.put("type", "qna");

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("QnA 스트리밍 시작 실패: lectureId={}, sectionIndex={}, cardIndex={}, qnaType={}", 
                    lectureId, sectionIndex, cardIndex, qnaType, e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }

    /**
     * Resource 스트리밍 시작
     * @param resourceType 선택적 파라미터: 타입이 제공되면 해당 타입의 Resource를 생성 (paper, wiki, video, blog)
     */
    @PostMapping("/start-resources-stream")
    public ResponseEntity<Map<String, Object>> startResourceStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam(required = false) String resourceType) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 고유 카드 ID 생성
            String cardId = String.format("resource_%d_%d_%d", lectureId, sectionIndex, cardIndex);

            // 비동기로 스트리밍 시작
            aiStreamingService.streamResource(lectureId, sectionIndex, cardIndex, cardId, resourceType);

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("cardId", cardId);
            response.put("type", "resource");

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Resource 스트리밍 시작 실패: lectureId={}, sectionIndex={}, cardIndex={}, resourceType={}", 
                    lectureId, sectionIndex, cardIndex, resourceType, e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(errorResponse);
        }
    }
}

