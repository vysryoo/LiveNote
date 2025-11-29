package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiStreamingService {

    private final StreamGateway streamGateway;
    private final SummaryService summaryService;

    // QnA 확장 카드 스트리밍
    @Async
    public void startQnaStreaming(Long lectureId, Integer sectionIndex, String cardId, String qnaType) {
        log.info("🚀 [Streaming] Start QnA: cardId={} type={}", cardId, qnaType);

        // 1. 요약 데이터 존재 여부 체크 (요구사항: 요약 실패 시 카드 생성 금지)
        // (SummaryService에 existsByLectureAndSection 메서드가 있다고 가정)
        if (!summaryService.existsByLectureAndSection(lectureId, sectionIndex)) {
            log.warn("❌ [Streaming] Summary not found. Aborting. lectureId={} section={}", lectureId, sectionIndex);
            streamGateway.sendError(lectureId, "요약 데이터가 없어 스트리밍을 시작할 수 없습니다.");
            return;
        }

        try {
            String questionTitle = "사용자가 선택한 " + qnaType + " 질문?"; // 제목 정의
            String mockAnswer = switch (qnaType) {
                case "advanced" -> "이 내용은 심화 학습이 필요한 주제입니다. 관련된 최신 연구 동향을 살펴보면...";
                case "application" -> "실생활에서는 이 개념이 자율주행 자동차의 센서 데이터 처리에 활용됩니다.";
                default -> "해당 질문에 대한 AI 심층 답변을 생성하고 있습니다. 잠시만 기다려 주세요.";
            };

            // 2. 토큰 전송 (title 포함, resourceType은 null)
            for (char c : mockAnswer.toCharArray()) {
                TimeUnit.MILLISECONDS.sleep(100); // 100ms 간격

                streamGateway.sendStreamToken(
                        lectureId,
                        "qna_stream",
                        cardId,
                        String.valueOf(c),
                        false,
                        null,
                        questionTitle, // ✅ title 전달
                        null           // ✅ QnA는 resourceType 없음
                );
            }

            // 3. 완료 메시지 전송
            Map<String, Object> finalData = Map.of(
                    "id", System.currentTimeMillis(),
                    "lectureId", lectureId,
                    "sectionIndex", sectionIndex,
                    "type", qnaType,
                    "question", questionTitle,
                    "answer", mockAnswer,
                    "createdAt", java.time.LocalDateTime.now().toString()
            );

            // 완료 시에는 title/type 굳이 안 보내도 됨 (null 처리)
            streamGateway.sendStreamToken(lectureId, "qna_stream", cardId, null, true, finalData, null, null);
            log.info("✅ [Streaming] QnA Completed: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
            streamGateway.sendError(lectureId, "Streaming failed: " + e.getMessage());
        }
    }

    // Resource 확장 카드 스트리밍
    @Async
    public void startResourceStreaming(Long lectureId, Integer sectionIndex, String cardId, String resourceType) {
        log.info("🚀 [Streaming] Start Resource: cardId={} type={}", cardId, resourceType);

        // [추가] 1. 요약 데이터 존재 여부 체크
        if (!summaryService.existsByLectureAndSection(lectureId, sectionIndex)) {
            log.warn("❌ [Streaming] Summary not found. Aborting. lectureId={} section={}", lectureId, sectionIndex);
            streamGateway.sendError(lectureId, "요약 데이터가 없어 스트리밍을 시작할 수 없습니다.");
            return;
        }

        try {
            String mockTitle = "추천 자료: " + resourceType + " 관련 핵심 가이드"; // 제목 정의
            String mockDescription = "이 자료는 해당 섹션의 내용을 보충하기 위해 AI가 선정한 " + resourceType + " 자료입니다...";

            // 2. 토큰 전송 (title과 resourceType 둘 다 전달)
            for (char c : mockDescription.toCharArray()) {
                TimeUnit.MILLISECONDS.sleep(80);

                streamGateway.sendStreamToken(
                        lectureId,
                        "resource_stream",
                        cardId,
                        String.valueOf(c),
                        false,
                        null,
                        mockTitle,    // ✅ title 전달
                        resourceType  // ✅ resourceType 전달
                );
            }

            // 3. 완료 메시지
            Map<String, Object> finalData = Map.of(
                    "id", System.currentTimeMillis(),
                    "lectureId", lectureId,
                    "sectionIndex", sectionIndex,
                    "type", resourceType,
                    "title", mockTitle,
                    "text", mockDescription,
                    "url", "https://example.com/ref/" + resourceType,
                    "score", 0.95
            );

            streamGateway.sendStreamToken(lectureId, "resource_stream", cardId, null, true, finalData, null, null);
            log.info("✅ [Streaming] Resource Completed: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
            streamGateway.sendError(lectureId, "Streaming failed: " + e.getMessage());
        }
    }
}
