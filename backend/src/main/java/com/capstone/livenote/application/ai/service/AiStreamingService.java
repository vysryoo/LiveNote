package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ws.StreamGateway;
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

    /**
     * QnA 확장 카드 스트리밍
     * - Controller는 이 메서드를 호출하고 즉시 반환됨 (Non-blocking)
     * - 여기서 별도 스레드로 텍스트를 생성하며 토큰을 전송
     */
    @Async
    public void startQnaStreaming(Long lectureId, Integer sectionIndex, String cardId, String qnaType) {
        log.info("🚀 [Streaming] Start QnA: cardId={} type={}", cardId, qnaType);

        try {
            // TODO: 실제 AI 모델(OpenAI/Claude) 연동 시 WebClient의 Flux<String> 등을 사용하여 토큰을 받습니다.
            // 현재는 프론트 연동 테스트를 위해 가상의 텍스트를 생성하여 스트리밍합니다.

            String mockAnswer = switch (qnaType) {
                case "advanced" -> "이 내용은 심화 학습이 필요한 주제입니다. 관련된 최신 연구 동향을 살펴보면...";
                case "application" -> "실생활에서는 이 개념이 자율주행 자동차의 센서 데이터 처리에 활용됩니다.";
                default -> "해당 질문에 대한 AI 심층 답변을 생성하고 있습니다. 잠시만 기다려 주세요.";
            };

            // 1. 토큰 단위 전송 시뮬레이션 (글자 단위 loop)
            for (char c : mockAnswer.toCharArray()) {
                // 100ms 지연 (타이핑 효과)
                TimeUnit.MILLISECONDS.sleep(100);

                // 토큰 전송 (isComplete = false)
                streamGateway.sendStreamToken(
                        lectureId,
                        "qna_stream",
                        cardId,
                        String.valueOf(c),
                        false,
                        null
                );
            }

            // 2. 완료 메시지 전송 (isComplete = true)
            // 최종적으로 저장될 데이터 구조를 함께 보냄
            Map<String, Object> finalData = Map.of(
                    "id", System.currentTimeMillis(), // 임시 ID
                    "lectureId", lectureId,
                    "sectionIndex", sectionIndex,
                    "type", qnaType,
                    "question", "사용자가 선택한 " + qnaType + " 질문",
                    "answer", mockAnswer,
                    "createdAt", java.time.LocalDateTime.now().toString()
            );

            streamGateway.sendStreamToken(
                    lectureId,
                    "qna_stream",
                    cardId,
                    null,
                    true,
                    finalData
            );

            log.info("✅ [Streaming] QnA Completed: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
            streamGateway.sendError(lectureId, "Streaming failed: " + e.getMessage());
        }
    }

    /**
     * Resource 확장 카드 스트리밍
     */
    @Async
    public void startResourceStreaming(Long lectureId, Integer sectionIndex, String cardId, String resourceType) {
        log.info("🚀 [Streaming] Start Resource: cardId={} type={}", cardId, resourceType);

        try {
            String mockTitle = "추천 자료: " + resourceType + " 관련 핵심 가이드";
            String mockDescription = "이 자료는 해당 섹션의 내용을 보충하기 위해 AI가 선정한 " + resourceType + " 자료입니다...";

            // 시뮬레이션: 설명 텍스트 스트리밍
            for (char c : mockDescription.toCharArray()) {
                TimeUnit.MILLISECONDS.sleep(80);
                streamGateway.sendStreamToken(
                        lectureId,
                        "resource_stream",
                        cardId,
                        String.valueOf(c),
                        false,
                        null
                );
            }

            // 완료 메시지
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

            streamGateway.sendStreamToken(
                    lectureId,
                    "resource_stream",
                    cardId,
                    null,
                    true,
                    finalData
            );

            log.info("✅ [Streaming] Resource Completed: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
            streamGateway.sendError(lectureId, "Streaming failed: " + e.getMessage());
        }
    }
}
