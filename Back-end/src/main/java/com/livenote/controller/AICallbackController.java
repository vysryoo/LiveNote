package com.livenote.controller;

import com.livenote.entity.*;
import com.livenote.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
public class AICallbackController {
    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final SummaryRepository summaryRepository;
    private final ResourceRepository resourceRepository;
    private final QnARepository qnARepository;

    @PostMapping("/callback")
    public ResponseEntity<Map<String, String>> aiCallback(@RequestBody Map<String, Object> payload) {
        try {
            String type = (String) payload.get("type");
            Map<String, Object> data = (Map<String, Object>) payload.get("data");
            Long lectureId = Long.valueOf(payload.get("lectureId").toString());
            Integer sectionIndex = Integer.valueOf(payload.get("sectionIndex").toString());

            Lecture lecture = lectureRepository.findById(lectureId)
                    .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

            switch (type) {
                case "transcript":
                    saveTranscript(lectureId, sectionIndex, data);
                    break;
                case "summary":
                    saveSummary(lectureId, sectionIndex, data);
                    break;
                case "resource":
                    saveResource(lectureId, sectionIndex, data);
                    break;
                case "qna":
                    saveQnA(lectureId, sectionIndex, data);
                    break;
                default:
                    log.warn("알 수 없는 타입: {}", type);
            }

            Map<String, String> response = new HashMap<>();
            response.put("message", "콜백 처리 완료");
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("AI 콜백 처리 오류", e);
            Map<String, String> response = new HashMap<>();
            response.put("message", "콜백 처리 실패: " + e.getMessage());
            return ResponseEntity.badRequest().body(response);
        }
    }

    private void saveTranscript(Long lectureId, Integer sectionIndex, Map<String, Object> data) {
        String text = getStringValue(data.get("content"));
        Double startSec = getDoubleValue(data.get("timestamp"));
        Double endSec = startSec != null ? startSec + 10.0 : null; // 예시

        Transcript transcript = Transcript.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .startSec(startSec)
                .endSec(endSec)
                .text(text)
                .build();

        transcriptRepository.save(transcript);
    }

    private void saveSummary(Long lectureId, Integer sectionIndex, Map<String, Object> data) {
        String text = getStringValue(data.get("content"));
        Double startSec = getDoubleValue(data.get("timestamp"));
        Double endSec = startSec != null ? startSec + 10.0 : null; // 예시

        Summary summary = Summary.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .startSec(startSec)
                .endSec(endSec)
                .text(text)
                .build();

        summaryRepository.save(summary);
    }

    private void saveResource(Long lectureId, Integer sectionIndex, Map<String, Object> data) {
        String typeStr = getStringValue(data.get("type"));
        String title = getStringValue(data.get("title"));
        String text = getStringValue(data.get("text"));
        String url = getStringValue(data.get("url"));
        String thumbnail = getStringValue(data.get("thumbnail"));
        Double score = getDoubleValue(data.get("score"));

        Resource.ResourceType resourceType = Resource.ResourceType.valueOf(typeStr != null ? typeStr : "blog");

        Resource resource = Resource.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .type(resourceType)
                .title(title)
                .text(text)
                .url(url)
                .thumbnail(thumbnail)
                .score(score)
                .build();

        resourceRepository.save(resource);
    }

    private void saveQnA(Long lectureId, Integer sectionIndex, Map<String, Object> data) {
        String typeStr = getStringValue(data.get("type"));
        String question = getStringValue(data.get("question"));
        String answer = getStringValue(data.get("answer"));

        QnA.QnAType qnAType = QnA.QnAType.valueOf(typeStr != null ? typeStr : "concept");

        QnA qnA = QnA.builder()
                .lectureId(lectureId)
                .sectionIndex(sectionIndex)
                .type(qnAType)
                .question(question)
                .answer(answer)
                .build();

        qnARepository.save(qnA);
    }

    private String getStringValue(Object value) {
        if (value == null) return null;
        if (value instanceof String) return (String) value;
        if (value instanceof String[]) {
            String[] arr = (String[]) value;
            return String.join(" ", arr);
        }
        return value.toString();
    }

    private Double getDoubleValue(Object value) {
        if (value == null) return null;
        if (value instanceof Number) return ((Number) value).doubleValue();
        if (value instanceof String) {
            try {
                return Double.parseDouble((String) value);
            } catch (NumberFormatException e) {
                return null;
            }
        }
        return null;
    }
}

