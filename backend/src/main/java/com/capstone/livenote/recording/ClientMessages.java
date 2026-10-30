package com.capstone.livenote.recording;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;
import java.util.Map;

/**
 * 녹음 WebSocket으로 브라우저에 보내는 메시지. 형식은 {@code {type, data}}이다.
 */
final class ClientMessages {

    private ClientMessages() {}

    static void sendTranscript(ObjectMapper objectMapper, WebSocketSession session, String content, boolean isFinal)
            throws IOException {
        String json = objectMapper.writeValueAsString(Map.of(
                "type", "transcript",
                "data", Map.of("content", content, "isFinal", isFinal)
        ));
        session.sendMessage(new TextMessage(json));
    }

    // 브라우저 연결이 이미 끊겼을 수 있어 전송 실패는 무시
    static void sendError(ObjectMapper objectMapper, WebSocketSession session, String message) {
        try {
            String json = objectMapper.writeValueAsString(
                    Map.of("type", "error", "data", Map.of("error", message))
            );
            session.sendMessage(new TextMessage(json));
        } catch (Exception ignored) {
        }
    }

    static void close(WebSocketSession session, CloseStatus status) {
        try {
            session.close(status);
        } catch (Exception ignored) {
        }
    }
}
