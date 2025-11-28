package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.entity.Summary;
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

    public void sendSummary(Summary summary) {
        sendSummary(
                summary.getLectureId(),
                summary.getSectionIndex(),
                summary.getText(),
                "final"
        );
    }

    public void sendSummary(Long lectureId, Integer sectionIndex, String text, String phase) {
        String destination = "/topic/lectures/" + lectureId + "/summary/" + sectionIndex;

        Map<String, Object> payload = Map.of(
                "type", "summary",
                "lectureId", lectureId,
                "sectionIndex", sectionIndex,
                "text", text != null ? text : "",
                "phase", phase != null ? phase : "final"
        );

        tmpl.convertAndSend(destination, payload);
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
    public void sendStreamToken(Long lectureId, String type, String cardId, String token, boolean isComplete, Object data, String title, String resourceType) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", type);         // "qna_stream" or "resource_stream"
        payload.put("cardId", cardId);
        payload.put("isComplete", isComplete);

        if (isComplete) {
            payload.put("data", data); // 완료 시엔 최종 데이터 객체 포함
        } else {
            payload.put("token", token); // 진행 중일 땐 글자 토큰

            //
            if (title != null) {
                payload.put("title", title);
            }
            if (resourceType != null) {
                payload.put("resourceType", resourceType);
            }
        }

        // 스트리밍 전용 토픽 경로로 전송
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/stream", payload);
    }
}

