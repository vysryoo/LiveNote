package com.capstone.livenote.application.ws;

import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class StreamGateway {
    private final SimpMessagingTemplate tmpl;

    public record WSMsg(String type, Map<String, Object> data) {}

    private String topic(Long lectureId) {
        return "/topic/lectures/" + lectureId + "/transcription";
    }

    public void sendTranscript(Long lectureId, Object content, boolean isFinal) {
        tmpl.convertAndSend(topic(lectureId),
                new WSMsg("transcript", Map.of(
                        "content", content,
                        "timestamp", System.currentTimeMillis(),
                        "isFinal", isFinal
                )));
    }

    public void sendSummary(Long lectureId, Object content) {
        tmpl.convertAndSend(topic(lectureId),
                new WSMsg("summary", Map.of(
                        "content", content,
                        "timestamp", System.currentTimeMillis()
                )));
    }

    public void sendResource(Long lectureId, Object content) {
        tmpl.convertAndSend(topic(lectureId),
                new WSMsg("resource", Map.of("content", content, "timestamp", System.currentTimeMillis())));
    }

    public void sendQna(Long lectureId, Object content) {
        tmpl.convertAndSend(topic(lectureId),
                new WSMsg("qna", Map.of("content", content, "timestamp", System.currentTimeMillis())));
    }

    public void sendError(Long lectureId, String message) {
        tmpl.convertAndSend(topic(lectureId),
                new WSMsg("error", Map.of("error", message)));
    }
}
