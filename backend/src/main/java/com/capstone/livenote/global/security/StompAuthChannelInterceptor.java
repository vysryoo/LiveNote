package com.capstone.livenote.global.security;

import com.capstone.livenote.domain.lecture.service.LectureService;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Component;

import java.security.Principal;
import java.util.Collections;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * STOMP 연결과 구독을 인증한다.
 *
 * 브라우저 WebSocket 핸드셰이크에는 Authorization 헤더를 붙일 수 없어 HTTP 필터 단계에서는 인증하지 않고,
 * STOMP CONNECT 프레임의 헤더로 사용자를 확인한다. 구독은 본인 강의의 토픽만 허용한다.
 * 토픽 메시지는 서버만 보내므로 클라이언트의 SEND는 거부한다.
 */
@Component
@RequiredArgsConstructor
public class StompAuthChannelInterceptor implements ChannelInterceptor {

    // 단어를 영문·숫자로 제한해 RabbitMQ 와일드카드(*, #)로 다른 강의 토픽을 구독하지 못하게 함
    private static final Pattern LECTURE_TOPIC = Pattern.compile("^/topic/lectures\\.(\\d+)(\\.[A-Za-z0-9]+)*$");
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtTokenProvider jwtTokenProvider;
    private final LectureService lectureService;

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null || accessor.getCommand() == null) {
            return message;
        }
        if (accessor.getCommand() == StompCommand.CONNECT) {
            accessor.setUser(authenticate(accessor.getFirstNativeHeader(AUTHORIZATION_HEADER)));
            // CONNECT 프레임은 RabbitMQ로 그대로 전달되므로 확인을 마친 토큰은 제거
            accessor.removeNativeHeader(AUTHORIZATION_HEADER);
        } else if (accessor.getCommand() == StompCommand.SUBSCRIBE) {
            authorizeSubscription(accessor.getUser(), accessor.getDestination());
        } else if (accessor.getCommand() == StompCommand.SEND) {
            throw new AccessDeniedException("client send not allowed");
        }
        return message;
    }

    private Principal authenticate(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith(BEARER_PREFIX)) {
            throw new AccessDeniedException("missing token");
        }
        String token = authorizationHeader.substring(BEARER_PREFIX.length());
        if (!jwtTokenProvider.validateToken(token)) {
            throw new AccessDeniedException("invalid token");
        }
        Long userId = jwtTokenProvider.getUserIdFromToken(token);
        return new UsernamePasswordAuthenticationToken(userId, null, Collections.emptyList());
    }

    private void authorizeSubscription(Principal user, String destination) {
        if (user == null) {
            throw new AccessDeniedException("not authenticated");
        }
        Long lectureId = lectureIdOf(destination)
                .orElseThrow(() -> new AccessDeniedException("unsupported destination"));
        try {
            lectureService.getOwned(lectureId, Long.parseLong(user.getName()));
        } catch (EntityNotFoundException e) {
            throw new AccessDeniedException("lecture not found");
        }
    }

    /**
     * 강의 토픽 주소에서 강의 ID를 꺼낸다.
     *
     * @param destination 구독 주소. 예: {@code /topic/lectures.4.summary}
     * @return 강의 ID. 강의 토픽 형식이 아니면 비어 있음
     */
    static Optional<Long> lectureIdOf(String destination) {
        if (destination == null) {
            return Optional.empty();
        }
        Matcher matcher = LECTURE_TOPIC.matcher(destination);
        return matcher.matches() ? Optional.of(Long.parseLong(matcher.group(1))) : Optional.empty();
    }
}
