package com.livenote.config;

import com.livenote.websocket.TranscriptionWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketHandlerConfig implements WebSocketConfigurer {
    private final TranscriptionWebSocketHandler transcriptionWebSocketHandler;

    public WebSocketHandlerConfig(TranscriptionWebSocketHandler transcriptionWebSocketHandler) {
        this.transcriptionWebSocketHandler = transcriptionWebSocketHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(transcriptionWebSocketHandler, "/ws/transcription")
                .setAllowedOrigins("*");
    }
}

