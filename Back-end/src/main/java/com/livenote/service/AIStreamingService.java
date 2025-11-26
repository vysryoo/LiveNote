package com.livenote.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.livenote.entity.Lecture;
import com.livenote.entity.QnA;
import com.livenote.entity.Resource;
import com.livenote.repository.LectureRepository;
import com.livenote.repository.QnARepository;
import com.livenote.repository.ResourceRepository;
import com.livenote.repository.TranscriptRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AIStreamingService {
    // 토큰 전송 간격 (밀리초) - 값이 클수록 느리게, 작을수록 빠르게
    private static final int TOKEN_SEND_INTERVAL_MS = 100;
    
    private final SimpMessagingTemplate messagingTemplate;
    private final OpenAIGenerationService openAIGenerationService;
    private final QnARepository qnARepository;
    private final ResourceRepository resourceRepository;
    private final TranscriptRepository transcriptRepository;
    private final LectureRepository lectureRepository;
    private final LectureService lectureService;
    private final ObjectMapper objectMapper;

    /**
     * QnA 스트리밍 시작
     * @param qnaType 타입이 제공되면 해당 타입의 QnA를 선택, null이면 cardIndex로 선택
     */
    public void streamQnA(Long lectureId, Integer sectionIndex, Integer cardIndex, String cardId, String qnaType) {
        CompletableFuture.runAsync(() -> {
            try {
                Lecture lecture = lectureRepository.findById(lectureId)
                        .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

                // 해당 섹션의 전사 내용 가져오기
                List<String> transcriptTexts = transcriptRepository
                        .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                        .stream()
                        .map(t -> t.getText() != null ? t.getText() : "")
                        .filter(text -> !text.isEmpty())
                        .collect(Collectors.toList());

                if (transcriptTexts.isEmpty()) {
                    sendError(lectureId, cardId, "qna", "전사 내용이 없습니다");
                    return;
                }

                String transcriptText = String.join(" ", transcriptTexts);
                String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";

                // OpenAI 스트리밍 호출 (간단한 구현 - 실제로는 스트리밍 API 사용)
                // 여기서는 generateQnA를 사용하고, 각 QnA를 토큰 단위로 시뮬레이션
                log.info("QnA 생성 시작: lectureId={}, sectionIndex={}, cardIndex={}, qnaType={}, transcriptLength={}", 
                    lectureId, sectionIndex, cardIndex, qnaType, transcriptText.length());
                List<Map<String, Object>> qnaList = openAIGenerationService.generateQnA(transcriptText, language);
                log.info("QnA 생성 결과: qnaList={}", qnaList != null ? qnaList.size() : "null");
                
                if (qnaList == null || qnaList.isEmpty()) {
                    log.error("QnA 생성 실패: qnaList가 null이거나 비어있음. transcriptText 길이: {}", transcriptText.length());
                    sendError(lectureId, cardId, "qna", "QnA 생성 실패: OpenAI API 응답이 비어있습니다");
                    return;
                }

                // 타입이 제공되면 해당 타입의 QnA 선택, 없으면 cardIndex로 선택
                Map<String, Object> qnaData = null;
                if (qnaType != null && !qnaType.isEmpty()) {
                    // 타입별로 선택
                    for (Map<String, Object> qna : qnaList) {
                        String type = getStringValue(qna.get("type"));
                        if (qnaType.equalsIgnoreCase(type)) {
                            qnaData = qna;
                            break;
                        }
                    }
                    if (qnaData == null) {
                        log.warn("해당 타입의 QnA를 찾을 수 없음: qnaType={}, 사용 가능한 타입: {}", 
                            qnaType, qnaList.stream().map(q -> getStringValue(q.get("type"))).collect(Collectors.toList()));
                        // 타입이 없으면 첫 번째 사용
                        qnaData = qnaList.get(0);
                    }
                } else {
                    // cardIndex로 선택 (기존 로직)
                    qnaData = qnaList.size() > cardIndex ? qnaList.get(cardIndex) : qnaList.get(0);
                }
                
                String question = getStringValue(qnaData.get("question"));
                String answer = getStringValue(qnaData.get("answer"));
                String type = getStringValue(qnaData.get("type"));

                // 답변을 토큰 단위로 시뮬레이션 전송
                if (answer != null && !answer.isEmpty()) {
                    String[] tokens = answer.split("");
                    for (String token : tokens) {
                        sendToken(lectureId, cardId, "qna", token, false);
                        try {
                            Thread.sleep(TOKEN_SEND_INTERVAL_MS); // 토큰 전송 간격
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            return;
                        }
                    }
                }

                // DB 저장
                QnA.QnAType qnAType = QnA.QnAType.valueOf(type != null ? type : "concept");
                QnA qna = QnA.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .type(qnAType)
                        .question(question)
                        .answer(answer)
                        .build();

                QnA savedQnA = qnARepository.save(qna);

                // 완료 메시지 전송
                sendComplete(lectureId, cardId, "qna", lectureService.toQnADto(savedQnA));

            } catch (Exception e) {
                log.error("QnA 스트리밍 실패: cardId={}", cardId, e);
                sendError(lectureId, cardId, "qna", e.getMessage());
            }
        });
    }

    /**
     * Resource 스트리밍 시작
     * @param resourceType 타입이 제공되면 해당 타입의 Resource를 선택, null이면 cardIndex로 선택
     */
    public void streamResource(Long lectureId, Integer sectionIndex, Integer cardIndex, String cardId, String resourceType) {
        CompletableFuture.runAsync(() -> {
            try {
                Lecture lecture = lectureRepository.findById(lectureId)
                        .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

                // 해당 섹션의 전사 내용 가져오기
                List<String> transcriptTexts = transcriptRepository
                        .findByLectureIdAndSectionIndex(lectureId, sectionIndex)
                        .stream()
                        .map(t -> t.getText() != null ? t.getText() : "")
                        .filter(text -> !text.isEmpty())
                        .collect(Collectors.toList());

                if (transcriptTexts.isEmpty()) {
                    sendError(lectureId, cardId, "resource", "전사 내용이 없습니다");
                    return;
                }

                String transcriptText = String.join(" ", transcriptTexts);
                String language = lecture.getSttLanguage() != null ? lecture.getSttLanguage() : "한국어";

                // OpenAI 호출
                List<Map<String, Object>> resourcesList = openAIGenerationService.generateResources(transcriptText, language);
                
                if (resourcesList == null || resourcesList.isEmpty()) {
                    sendError(lectureId, cardId, "resource", "자료 생성 실패");
                    return;
                }

                // 타입이 제공되면 해당 타입의 Resource 선택, 없으면 cardIndex로 선택
                Map<String, Object> resourceData = null;
                if (resourceType != null && !resourceType.isEmpty()) {
                    // 타입별로 선택
                    for (Map<String, Object> resource : resourcesList) {
                        String type = getStringValue(resource.get("type"));
                        if (resourceType.equalsIgnoreCase(type)) {
                            resourceData = resource;
                            break;
                        }
                    }
                    if (resourceData == null) {
                        log.warn("해당 타입의 Resource를 찾을 수 없음: resourceType={}, 사용 가능한 타입: {}", 
                            resourceType, resourcesList.stream().map(r -> getStringValue(r.get("type"))).collect(Collectors.toList()));
                        // 타입이 없으면 첫 번째 사용
                        resourceData = resourcesList.get(0);
                    }
                } else {
                    // cardIndex로 선택 (기존 로직)
                    resourceData = resourcesList.size() > cardIndex ? resourcesList.get(cardIndex) : resourcesList.get(0);
                }
                
                String typeStr = getStringValue(resourceData.get("type"));
                String title = getStringValue(resourceData.get("title"));
                String text = getStringValue(resourceData.get("text"));
                String url = getStringValue(resourceData.get("url"));
                String thumbnail = getStringValue(resourceData.get("thumbnail"));
                Double score = resourceData.get("score") instanceof Number 
                    ? ((Number) resourceData.get("score")).doubleValue() 
                    : null;

                // 텍스트를 토큰 단위로 시뮬레이션 전송
                if (text != null && !text.isEmpty()) {
                    String[] tokens = text.split("");
                    for (String token : tokens) {
                        sendToken(lectureId, cardId, "resource", token, false);
                        try {
                            Thread.sleep(TOKEN_SEND_INTERVAL_MS); // 토큰 전송 간격
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                            return;
                        }
                    }
                }

                // DB 저장
                Resource.ResourceType savedResourceType = Resource.ResourceType.valueOf(typeStr != null ? typeStr : "blog");
                Resource resource = Resource.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .type(savedResourceType)
                        .title(title)
                        .text(text)
                        .url(url)
                        .thumbnail(thumbnail)
                        .score(score)
                        .build();

                Resource savedResource = resourceRepository.save(resource);

                // 완료 메시지 전송
                sendComplete(lectureId, cardId, "resource", lectureService.toResourceDto(savedResource));

            } catch (Exception e) {
                log.error("Resource 스트리밍 실패: cardId={}", cardId, e);
                sendError(lectureId, cardId, "resource", e.getMessage());
            }
        });
    }

    /**
     * 토큰 전송
     */
    private void sendToken(Long lectureId, String cardId, String type, String token, boolean isComplete) {
        try {
            ObjectNode message = objectMapper.createObjectNode();
            message.put("type", type + "_stream");
            message.put("cardId", cardId);
            message.put("token", token);
            message.put("isComplete", isComplete);

            messagingTemplate.convertAndSend(
                    "/topic/lectures/" + lectureId + "/stream",
                    message
            );
        } catch (Exception e) {
            log.error("토큰 전송 실패: cardId={}", cardId, e);
        }
    }

    /**
     * 완료 메시지 전송
     */
    private void sendComplete(Long lectureId, String cardId, String type, Object data) {
        try {
            ObjectNode message = objectMapper.createObjectNode();
            message.put("type", type + "_stream");
            message.put("cardId", cardId);
            message.put("isComplete", true);
            message.set("data", objectMapper.valueToTree(data));

            messagingTemplate.convertAndSend(
                    "/topic/lectures/" + lectureId + "/stream",
                    message
            );
        } catch (Exception e) {
            log.error("완료 메시지 전송 실패: cardId={}", cardId, e);
        }
    }

    /**
     * 에러 전송
     */
    private void sendError(Long lectureId, String cardId, String type, String error) {
        try {
            ObjectNode message = objectMapper.createObjectNode();
            message.put("type", type + "_stream");
            message.put("cardId", cardId);
            message.put("isComplete", true);
            message.put("error", error);

            messagingTemplate.convertAndSend(
                    "/topic/lectures/" + lectureId + "/stream",
                    message
            );
        } catch (Exception e) {
            log.error("에러 메시지 전송 실패: cardId={}", cardId, e);
        }
    }

    private String getStringValue(Object value) {
        if (value == null) return null;
        if (value instanceof String) return (String) value;
        if (value instanceof List) {
            List<?> list = (List<?>) value;
            return list.stream()
                    .map(Object::toString)
                    .collect(Collectors.joining(" "));
        }
        return value.toString();
    }
}

