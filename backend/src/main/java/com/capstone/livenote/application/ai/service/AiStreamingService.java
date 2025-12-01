package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiStreamingService {

    private final StreamGateway streamGateway;
    private final SummaryService summaryService;
    private final QnaRepository qnaRepository;
    private final ResourceRepository resourceRepository;

    // QnA 확장 카드 스트리밍
    @Async
    public void startQnaStreaming(Long lectureId, Integer sectionIndex, String cardId, String qnaType) {
        log.info("🚀 [Streaming] Start QnA: cardId={} type={}", cardId, qnaType);

        if (!summaryService.existsByLectureAndSection(lectureId, sectionIndex)) {
            streamGateway.sendError(lectureId, "요약 데이터가 없어 스트리밍을 시작할 수 없습니다.");
            return;
        }

        try {
            // ... (Mock 데이터 생성 로직 유지) ...
            String questionTitle = "사용자가 선택한 " + qnaType + " 질문?";
            String mockAnswer = "이 내용은 AI가 실시간으로 생성한 답변입니다...";

            // 1. 토큰 전송 (Streaming)
            for (char c : mockAnswer.toCharArray()) {
                TimeUnit.MILLISECONDS.sleep(50); // 속도 조절
                streamGateway.sendStreamToken(
                        lectureId, "qna_stream", cardId, String.valueOf(c), false, null, questionTitle, null
                );
            }

            // 2. DB 저장 (완료된 데이터)
            Qna savedQna = qnaRepository.save(
                    Qna.builder()
                            .lectureId(lectureId)
                            .sectionIndex(sectionIndex)
                            .type(resolveQnaType(qnaType)) // 타입 변환 필요
                            .question(questionTitle)
                            .answer(mockAnswer)
                            .build()
            );

            // 3. 완료 메시지 전송 (/stream)
            // 프론트엔드가 이 데이터를 받아서 카드를 '완료 상태'로 바꿈
            Map<String, Object> finalData = Map.of(
                    "id", savedQna.getId(),
                    "lectureId", lectureId,
                    "sectionIndex", sectionIndex,
                    "type", qnaType,
                    "question", questionTitle,
                    "answer", mockAnswer
            );
            streamGateway.sendStreamToken(lectureId, "qna_stream", cardId, null, true, finalData, null, null);

            // 4. 전체 리스트 브로드캐스트 (/qna)
            List<QnaResponseDto> allQnas = qnaRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .stream().map(QnaResponseDto::from).toList();
            streamGateway.sendQna(lectureId, sectionIndex, allQnas);

            log.info("✅ [Streaming] QnA Completed & Saved: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
            streamGateway.sendError(lectureId, "Streaming failed: " + e.getMessage());
        }
    }

    // Resource 확장 카드 스트리밍
    @Async
    public void startResourceStreaming(Long lectureId, Integer sectionIndex, String cardId, String resourceType) {
        log.info("🚀 [Streaming] Start Resource: cardId={} type={}", cardId, resourceType);

        if (!summaryService.existsByLectureAndSection(lectureId, sectionIndex)) {
            streamGateway.sendError(lectureId, "요약 데이터가 없어 스트리밍을 시작할 수 없습니다.");
            return;
        }

        try {
            String mockTitle = "추천 자료: " + resourceType;
            String mockDesc = "AI가 추천하는 자료입니다...";

            // 1. 토큰 전송
            for (char c : mockDesc.toCharArray()) {
                TimeUnit.MILLISECONDS.sleep(50);
                streamGateway.sendStreamToken(
                        lectureId, "resource_stream", cardId, String.valueOf(c), false, null, mockTitle, resourceType
                );
            }

            // 2. DB 저장
            Resource savedResource = resourceRepository.save(
                    Resource.builder()
                            .lectureId(lectureId)
                            .sectionIndex(sectionIndex)
                            .type(resolveResourceType(resourceType))
                            .title(mockTitle)
                            .text(mockDesc)
                            .url("https://example.com")
                            .score(0.9)
                            .build()
            );

            // 3. 완료 메시지 전송 (/stream)
            Map<String, Object> finalData = Map.of(
                    "id", savedResource.getId(),
                    "lectureId", lectureId,
                    "type", resourceType,
                    "title", mockTitle,
                    "text", mockDesc
            );
            streamGateway.sendStreamToken(lectureId, "resource_stream", cardId, null, true, finalData, null, null);

            // 4. 전체 리스트 브로드캐스트 (/resources)
            List<ResourceResponseDto> allResources = resourceRepository.findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                    .stream().map(ResourceResponseDto::from).toList();
            streamGateway.sendResources(lectureId, sectionIndex, allResources);

            log.info("✅ [Streaming] Resource Completed & Saved: {}", cardId);

        } catch (Exception e) {
            log.error("❌ [Streaming] Error: {}", e.getMessage());
        }
    }

    private Qna.Type resolveQnaType(String type) {
        if (type == null || type.isBlank()) {
            return Qna.Type.CONCEPT; // 기본값
        }

        return switch (type.trim().toLowerCase()) {
            case "application" -> Qna.Type.APPLICATION;
            case "advanced" -> Qna.Type.ADVANCED;
            case "comparison" -> Qna.Type.COMPARISON;
            case "concept" -> Qna.Type.CONCEPT;
            default -> Qna.Type.CONCEPT;
        };
    }

    private Resource.Type resolveResourceType(String type) {
        if (type == null || type.isBlank()) {
            return Resource.Type.WIKI; // 기본값
        }

        return switch (type.trim().toLowerCase()) {
            case "video" -> Resource.Type.VIDEO;
            case "blog" -> Resource.Type.BLOG;
            case "paper" -> Resource.Type.PAPER;
            case "wiki" -> Resource.Type.WIKI;
            default -> Resource.Type.WIKI;
        };
    }
}
