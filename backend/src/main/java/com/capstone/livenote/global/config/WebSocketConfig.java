package com.capstone.livenote.global.config;

import com.capstone.livenote.application.ws.RealtimeTranscriptionWebSocketHandler;
import com.capstone.livenote.global.security.StompAuthChannelInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
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

    private final RealtimeTranscriptionWebSocketHandler realtimeTranscriptionWebSocketHandler;
    private final StompAuthChannelInterceptor stompAuthChannelInterceptor;

    @Value("${app.stomp-relay.host}")
    private String relayHost;

    @Value("${app.stomp-relay.port}")
    private int relayPort;

    @Value("${app.stomp-relay.login}")
    private String relayLogin;

    @Value("${app.stomp-relay.passcode}")
    private String relayPasscode;

    @Value("${app.stomp-relay.virtual-host}")
    private String relayVirtualHost;

    @Override
    public void configureClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(stompAuthChannelInterceptor);
    }

    // 백엔드 인스턴스가 여러 개여도 모든 구독자에게 전달되도록 구독 관리를 RabbitMQ에 맡김
    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableStompBrokerRelay("/topic")
                .setRelayHost(relayHost)
                .setRelayPort(relayPort)
                .setClientLogin(relayLogin)
                .setClientPasscode(relayPasscode)
                .setSystemLogin(relayLogin)
                .setSystemPasscode(relayPasscode)
                .setVirtualHost(relayVirtualHost);
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 프론트 STOMP용 기본 엔드포인트 (/ws)
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*");
    }

    // === WebSocket 설정 (새로 추가: 오디오 업로드용) ===
    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        // OpenAI Realtime STT 중계용 WebSocket 엔드포인트 (프론트 경로: /ws/transcription)
        registry.addHandler(realtimeTranscriptionWebSocketHandler, "/ws/transcription")
                .setAllowedOrigins("*");
    }
}
