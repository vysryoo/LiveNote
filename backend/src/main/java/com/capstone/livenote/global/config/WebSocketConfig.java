package com.capstone.livenote.global.config;

import com.capstone.livenote.application.ws.AudioWebSocketHandler;
import com.capstone.livenote.application.ws.RealtimeTranscriptionWebSocketHandler;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocket
@EnableWebSocketMessageBroker
@RequiredArgsConstructor
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer, WebSocketConfigurer {

    private final AudioWebSocketHandler audioWebSocketHandler;
    private final RealtimeTranscriptionWebSocketHandler realtimeTranscriptionWebSocketHandler;

    // === STOMP 설정 (기존: 결과 전송용) ===
    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic");
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 기존: 전사/요약/자료/QnA 결과 수신용
        registry.addEndpoint("/api/ws/transcription")
                .setAllowedOriginPatterns("*");

        // 프론트 STOMP용 기본 엔드포인트 (/ws)
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*");
    }

    // === WebSocket 설정 (새로 추가: 오디오 업로드용) ===
    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        // 오디오 스트리밍 전용 WebSocket 엔드포인트
        registry.addHandler(audioWebSocketHandler, "/api/ws/audio")
                .setAllowedOrigins("*");

        // OpenAI Realtime STT 중계용 WebSocket 엔드포인트 (프론트 경로: /ws/transcription)
        registry.addHandler(realtimeTranscriptionWebSocketHandler, "/ws/transcription")
                .setAllowedOrigins("*");
    }
}
