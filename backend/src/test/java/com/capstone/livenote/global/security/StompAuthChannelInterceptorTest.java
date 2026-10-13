package com.capstone.livenote.global.security;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.service.LectureService;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;

import java.security.Principal;
import java.util.Collections;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class StompAuthChannelInterceptorTest {

    @Mock JwtTokenProvider jwtTokenProvider;
    @Mock LectureService lectureService;

    @InjectMocks
    StompAuthChannelInterceptor interceptor;

    private final MessageChannel channel = mock(MessageChannel.class);

    private Message<byte[]> connect(String authorization) {
        StompHeaderAccessor accessor = StompHeaderAccessor.create(StompCommand.CONNECT);
        if (authorization != null) {
            accessor.setNativeHeader("Authorization", authorization);
        }
        accessor.setLeaveMutable(true);
        return MessageBuilder.createMessage(new byte[0], accessor.getMessageHeaders());
    }

    private Message<byte[]> subscribe(Principal user, String destination) {
        StompHeaderAccessor accessor = StompHeaderAccessor.create(StompCommand.SUBSCRIBE);
        accessor.setUser(user);
        accessor.setDestination(destination);
        accessor.setLeaveMutable(true);
        return MessageBuilder.createMessage(new byte[0], accessor.getMessageHeaders());
    }

    private Principal user(long userId) {
        return new UsernamePasswordAuthenticationToken(userId, null, Collections.emptyList());
    }

    @Test
    void connect_withValidToken_setsUser() {
        when(jwtTokenProvider.validateToken("good")).thenReturn(true);
        when(jwtTokenProvider.getUserIdFromToken("good")).thenReturn(1L);

        Message<?> result = interceptor.preSend(connect("Bearer good"), channel);

        Principal principal = MessageHeaderAccessor.getAccessor(result, StompHeaderAccessor.class).getUser();
        assertThat(principal).isNotNull();
        assertThat(principal.getName()).isEqualTo("1");
    }

    @Test
    void connect_withoutToken_isRejected() {
        assertThatThrownBy(() -> interceptor.preSend(connect(null), channel))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void connect_withInvalidToken_isRejected() {
        when(jwtTokenProvider.validateToken("bad")).thenReturn(false);

        assertThatThrownBy(() -> interceptor.preSend(connect("Bearer bad"), channel))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void subscribe_toOwnLecture_isAllowed() {
        when(lectureService.getOwned(4L, 1L)).thenReturn(Lecture.builder().id(4L).userId(1L).build());

        Message<byte[]> message = subscribe(user(1L), "/topic/lectures/4/summary");

        assertThat(interceptor.preSend(message, channel)).isSameAs(message);
    }

    @Test
    void subscribe_toOtherUsersLecture_isRejected() {
        when(lectureService.getOwned(4L, 2L)).thenThrow(new EntityNotFoundException("lecture"));

        assertThatThrownBy(() -> interceptor.preSend(subscribe(user(2L), "/topic/lectures/4/stream"), channel))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void subscribe_withoutConnectedUser_isRejected() {
        assertThatThrownBy(() -> interceptor.preSend(subscribe(null, "/topic/lectures/4/summary"), channel))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void subscribe_toNonLectureTopic_isRejected() {
        assertThatThrownBy(() -> interceptor.preSend(subscribe(user(1L), "/topic/other"), channel))
                .isInstanceOf(AccessDeniedException.class);
    }

    @Test
    void lectureIdOf_parsesLectureTopics() {
        assertThat(StompAuthChannelInterceptor.lectureIdOf("/topic/lectures/12/summary/3")).contains(12L);
        assertThat(StompAuthChannelInterceptor.lectureIdOf("/topic/lectures/12")).contains(12L);
        assertThat(StompAuthChannelInterceptor.lectureIdOf("/topic/lectures/abc/summary")).isEqualTo(Optional.empty());
        assertThat(StompAuthChannelInterceptor.lectureIdOf(null)).isEqualTo(Optional.empty());
    }
}
