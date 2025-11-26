package com.livenote.controller;

import com.livenote.dto.SummaryDto;
import com.livenote.entity.Lecture;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.TranscriptRepository;
import com.livenote.service.OpenAIGenerationService;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
public class AIGenerationController {
    private final OpenAIGenerationService openAIGenerationService;
    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final AICallbackController aiCallbackController;

    @PostMapping("/generate-summary")
    public ResponseEntity<Map<String, Object>> generateSummary(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam(required = false) String phase) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 해당 섹션의 전사 내용 가져오기
            List<String> transcriptTexts = transcriptRepository
                    .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .stream()
                    .map(t -> t.getText() != null ? t.getText() : "")
                    .filter(text -> !text.isEmpty())
                    .collect(Collectors.toList());

            if (transcriptTexts.isEmpty()) {
                throw new RuntimeException("전사 내용이 없습니다");
            }

            String transcriptText = String.join(" ", transcriptTexts);
            String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";

            // 요약 생성
            String summaryText = openAIGenerationService.generateSummary(transcriptText, language);

            // phase에 따라 처리
            if ("partial".equals(phase)) {
                // 15초 경과 시: 요약은 DB 저장 안함 (프론트 표시용만)
                // 요약을 기반으로 자료탐색 2개, AI질문 2개 생성 후 DB 저장
                
                // 요약 기반으로 자료 추천 생성 (2개만)
                List<Map<String, Object>> resourcesList = openAIGenerationService.generateResources(summaryText, language);
                List<Map<String, Object>> resourcesToSave = resourcesList.stream()
                        .limit(2)
                        .collect(Collectors.toList());
                
                // 자료 저장
                for (Map<String, Object> resource : resourcesToSave) {
                    Map<String, Object> data = new HashMap<>();
                    data.put("type", resource.get("type"));
                    data.put("title", resource.get("title"));
                    data.put("text", resource.get("text"));
                    data.put("url", resource.get("url"));
                    data.put("thumbnail", resource.get("thumbnail"));
                    data.put("score", resource.get("score"));

                    Map<String, Object> payload = new HashMap<>();
                    payload.put("type", "resource");
                    payload.put("lectureId", lectureId);
                    payload.put("sectionIndex", sectionIndex);
                    payload.put("data", data);

                    aiCallbackController.aiCallback(payload);
                }

                // 요약 기반으로 질문 생성 (2개만)
                List<Map<String, Object>> qnaList = openAIGenerationService.generateQnA(summaryText, language);
                List<Map<String, Object>> qnaToSave = qnaList.stream()
                        .limit(2)
                        .collect(Collectors.toList());
                
                // 질문 저장
                for (Map<String, Object> qna : qnaToSave) {
                    Map<String, Object> data = new HashMap<>();
                    data.put("type", qna.get("type"));
                    data.put("question", qna.get("question"));
                    data.put("answer", qna.get("answer"));

                    Map<String, Object> payload = new HashMap<>();
                    payload.put("type", "qna");
                    payload.put("lectureId", lectureId);
                    payload.put("sectionIndex", sectionIndex);
                    payload.put("data", data);

                    aiCallbackController.aiCallback(payload);
                }

                log.info("15초 요약 완료: lectureId={}, sectionIndex={}, 자료 {}개, 질문 {}개 저장", 
                        lectureId, sectionIndex, resourcesToSave.size(), qnaToSave.size());
                
            } else if ("final".equals(phase)) {
                // 30초 경과 시: 요약은 DB에 저장
                Map<String, Object> data = new HashMap<>();
                data.put("content", summaryText);
                data.put("timestamp", (double) (sectionIndex * 30)); // 30초 단위

                Map<String, Object> payload = new HashMap<>();
                payload.put("type", "summary");
                payload.put("lectureId", lectureId);
                payload.put("sectionIndex", sectionIndex);
                payload.put("data", data);

                aiCallbackController.aiCallback(payload);
                log.info("30초 요약 저장 완료: lectureId={}, sectionIndex={}", lectureId, sectionIndex);
            }

            // SummaryDto 생성 (DB 저장 전이므로 id는 null)
            SummaryDto summaryDto = SummaryDto.builder()
                    .id(null) // DB 저장 후 id 생성됨
                    .lectureId(lectureId)
                    .sectionIndex(sectionIndex)
                    .startSec((double) (sectionIndex * 30))
                    .endSec((double) (sectionIndex * 30 + 30))
                    .text(summaryText)
                    .build();

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("summary", summaryDto);
            response.put("sectionIndex", sectionIndex);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("요약 생성 실패", e);
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }

    @PostMapping("/generate-qna")
    public ResponseEntity<Map<String, Object>> generateQnA(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 해당 섹션의 전사 내용 가져오기
            List<String> transcriptTexts = transcriptRepository
                    .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .stream()
                    .map(t -> t.getText() != null ? t.getText() : "")
                    .filter(text -> !text.isEmpty())
                    .collect(Collectors.toList());

            if (transcriptTexts.isEmpty()) {
                throw new RuntimeException("전사 내용이 없습니다");
            }

            String transcriptText = String.join(" ", transcriptTexts);
            String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";

            // 질문 생성 (각 유형별로 1개씩)
            List<Map<String, Object>> qnaList = openAIGenerationService.generateQnA(transcriptText, language);
            
            // 각 유형별로 1개씩만 선택 (concept, application, advanced, comparison)
            String[] qnaTypes = {"concept", "application", "advanced", "comparison"};
            Map<String, Map<String, Object>> selectedQnAs = new HashMap<>();
            
            // 먼저 각 유형별로 1개씩 선택
            for (Map<String, Object> qna : qnaList) {
                String type = (String) qna.get("type");
                if (type != null && !selectedQnAs.containsKey(type)) {
                    selectedQnAs.put(type, qna);
                }
            }
            
            // 각 유형별로 저장 (없으면 건너뜀)
            List<Map<String, Object>> savedQnAs = new ArrayList<>();
            for (String type : qnaTypes) {
                Map<String, Object> qna = selectedQnAs.get(type);
                if (qna != null) {
                    Map<String, Object> data = new HashMap<>();
                    data.put("type", qna.get("type"));
                    data.put("question", qna.get("question"));
                    data.put("answer", qna.get("answer"));

                    Map<String, Object> payload = new HashMap<>();
                    payload.put("type", "qna");
                    payload.put("lectureId", lectureId);
                    payload.put("sectionIndex", sectionIndex);
                    payload.put("data", data);

                    aiCallbackController.aiCallback(payload);
                    savedQnAs.add(qna);
                }
            }

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("qna", savedQnAs); // 필터링된 결과만 반환
            response.put("sectionIndex", sectionIndex);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("질문 생성 실패", e);
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }

    @PostMapping("/generate-resources")
    public ResponseEntity<Map<String, Object>> generateResources(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex) {
        try {
            Long userId = SecurityUtil.getCurrentUserId();
            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            if (!lecture.getUserId().equals(userId)) {
                throw new RuntimeException("권한이 없습니다");
            }

            // 해당 섹션의 전사 내용 가져오기
            List<String> transcriptTexts = transcriptRepository
                    .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .stream()
                    .map(t -> t.getText() != null ? t.getText() : "")
                    .filter(text -> !text.isEmpty())
                    .collect(Collectors.toList());

            if (transcriptTexts.isEmpty()) {
                throw new RuntimeException("전사 내용이 없습니다");
            }

            String transcriptText = String.join(" ", transcriptTexts);
            String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";

            // 자료 추천 생성 (각 소스별로 1개씩)
            List<Map<String, Object>> resourcesList = openAIGenerationService.generateResources(transcriptText, language);
            
            // 각 소스별로 1개씩만 선택 (paper, wiki, video, blog)
            String[] resourceTypes = {"paper", "wiki", "video", "blog"};
            Map<String, Map<String, Object>> selectedResources = new HashMap<>();
            
            // 먼저 각 소스별로 1개씩 선택
            for (Map<String, Object> resource : resourcesList) {
                String type = (String) resource.get("type");
                if (type != null && !selectedResources.containsKey(type)) {
                    selectedResources.put(type, resource);
                }
            }
            
            // 각 소스별로 저장 (없으면 건너뜀)
            List<Map<String, Object>> savedResources = new ArrayList<>();
            for (String type : resourceTypes) {
                Map<String, Object> resource = selectedResources.get(type);
                if (resource != null) {
                    Map<String, Object> data = new HashMap<>();
                    data.put("type", resource.get("type"));
                    data.put("title", resource.get("title"));
                    data.put("text", resource.get("text"));
                    data.put("url", resource.get("url"));
                    data.put("thumbnail", resource.get("thumbnail"));
                    data.put("score", resource.get("score"));

                    Map<String, Object> payload = new HashMap<>();
                    payload.put("type", "resource");
                    payload.put("lectureId", lectureId);
                    payload.put("sectionIndex", sectionIndex);
                    payload.put("data", data);

                    aiCallbackController.aiCallback(payload);
                    savedResources.add(resource);
                }
            }

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("resources", savedResources); // 필터링된 결과만 반환
            response.put("sectionIndex", sectionIndex);

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("자료 추천 생성 실패", e);
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }
}

