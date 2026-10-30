package com.capstone.livenote.global.config;

import com.capstone.livenote.global.security.StompAuthChannelInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * 브라우저로 실시간 메시지를 보내는 STOMP 설정.
 *
 * 녹음 WebSocket 설정({@link TranscriptionSocketConfig})과 나눠 둔다. 한 클래스에 두면 녹음 핸들러가 STOMP 전송
 * 빈을 거쳐 다시 이 설정을 필요로 하는 순환이 생긴다.
 */
@Configuration
@EnableWebSocketMessageBroker
@RequiredArgsConstructor
public class StompConfig implements WebSocketMessageBrokerConfigurer {

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
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*");
    }
}
