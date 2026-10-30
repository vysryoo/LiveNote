package com.capstone.livenote.global.config;

import com.capstone.livenote.application.ws.RealtimeTranscriptionWebSocketHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

/**
 * 브라우저의 녹음 음성을 받는 WebSocket 엔드포인트({@code /ws/transcription}) 설정.
 */
@Configuration
@EnableWebSocket
@RequiredArgsConstructor
public class TranscriptionSocketConfig implements WebSocketConfigurer {

    private final RealtimeTranscriptionWebSocketHandler realtimeTranscriptionWebSocketHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(realtimeTranscriptionWebSocketHandler, "/ws/transcription")
                .setAllowedOrigins("*");
    }
}
