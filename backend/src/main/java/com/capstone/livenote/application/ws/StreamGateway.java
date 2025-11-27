package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class StreamGateway {
    private final SimpMessagingTemplate tmpl;

    // 실시간 전사 전송
    public void sendTranscript(Long lectureId, TranscriptResponseDto dto, boolean isFinal) {
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/transcripts",
                Map.of(
                        "type", "transcript",
                        "lectureId", lectureId,
                        "sectionIndex", dto.getSectionIndex(),
                        "startSec", dto.getStartSec(),
                        "endSec", dto.getEndSec(),
                        "text", dto.getText(),
                        "isFinal", isFinal
                ));
    }

    // summary 실시간 전송
    public void sendSummary(Long lectureId,
                            Integer sectionIndex,
                            String text,
                            String phase) {

        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/summary",
                Map.of(
                        "type", "summary",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "phase", phase,
                        "text", text
                ));
    }


    // resource 실시간 전송
    public void sendResources(Long lectureId, Integer sectionIndex, List<ResourceResponseDto> items) {
        tmpl.convertAndSend(
                "/topic/lectures/" + lectureId + "/resources",
                Map.of(
                        "type", "resources",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }


    // qna 실시간 전송
    public void sendQna(Long lectureId, Integer sectionIndex, List<QnaResponseDto> items) {
        tmpl.convertAndSend(
                "/topic/lectures/" + lectureId + "/qna",
                Map.of(
                        "type", "qna",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }

    // error 전송
    public void sendError(Long lectureId, String error) {
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/error",
                Map.of("type", "error", "message", error));
    }

    // 스트리밍 토큰 전송 메소드
    public void sendStreamToken(Long lectureId, String type, String cardId, String token, boolean isComplete, Object data) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", type);         // "qna_stream" or "resource_stream"
        payload.put("cardId", cardId);
        payload.put("isComplete", isComplete);

        if (isComplete) {
            // 완료 시 최종 데이터 포함
            payload.put("data", data);
        } else {
            // 진행 중일 땐 토큰만 포함
            payload.put("token", token);
        }

        // 스트리밍 전용 토픽 경로로 전송
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/stream", payload);
    }
}

