package com.capstone.livenote.global.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.*;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // 프론트에서 구독하는 prefix
        registry.enableSimpleBroker("/topic");
        // 클라이언트에서 서버로 보낼 때 사용하는 prefix
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 고정 엔드포인트 + SockJS
        registry.addEndpoint("/api/ws/transcription")
                .setAllowedOriginPatterns("*")
                .withSockJS();
    }
}
