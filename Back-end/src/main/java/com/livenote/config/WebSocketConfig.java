package com.livenote.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Slf4j
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // 클라이언트가 구독할 수 있는 토픽 프리픽스
        config.enableSimpleBroker("/topic");
        // 클라이언트가 메시지를 보낼 때 사용하는 프리픽스
        config.setApplicationDestinationPrefixes("/app");
        log.info("STOMP 메시지 브로커 설정 완료: /topic, /app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // STOMP 엔드포인트 등록
        // 순수 WebSocket 사용 (SockJS 없이)
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")  // setAllowedOrigins 대신 setAllowedOriginPatterns 사용
                .setHandshakeHandler(new org.springframework.web.socket.server.support.DefaultHandshakeHandler());  // 기본 핸드셰이크 핸들러
        log.info("STOMP 엔드포인트 등록 완료: /ws (순수 WebSocket)");
    }
}

