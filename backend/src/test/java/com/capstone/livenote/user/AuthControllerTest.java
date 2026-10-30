package com.capstone.livenote.user;

import com.capstone.livenote.global.security.JwtTokenProvider;
import com.capstone.livenote.global.security.RefreshTokenService;
import com.capstone.livenote.global.security.RefreshTokenService.Rotation;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.time.Duration;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    @Mock UserService userService;
    @Mock RefreshTokenService refreshTokenService;
    @Mock JwtTokenProvider jwtTokenProvider;

    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        AuthController controller = new AuthController(userService, refreshTokenService, jwtTokenProvider);
        ReflectionTestUtils.setField(controller, "refreshCookieSecure", true);
        mvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    void login_returnsAccessTokenAndSetsHttpOnlyRefreshCookie() throws Exception {
        when(userService.login(any())).thenReturn(
                new AuthResponseDto("access", new UserViewDto(7L, "id", "name", "e@x.com", "ko")));
        when(refreshTokenService.issue(7L)).thenReturn("refresh");
        when(refreshTokenService.validity()).thenReturn(Duration.ofDays(14));

        String cookie = mvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"loginId\":\"id\",\"password\":\"pw\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.token").value("access"))
                .andReturn().getResponse().getHeader(HttpHeaders.SET_COOKIE);

        assertThat(cookie).startsWith("livenote_refresh=refresh")
                .contains("Path=/api/auth", "HttpOnly", "Secure", "SameSite=Strict", "Max-Age=1209600");
    }

    @Test
    void refresh_withValidCookie_issuesNewTokens() throws Exception {
        when(refreshTokenService.rotate("old")).thenReturn(Optional.of(new Rotation(7L, "new")));
        when(refreshTokenService.validity()).thenReturn(Duration.ofDays(14));
        when(jwtTokenProvider.createToken(7L)).thenReturn("access2");

        String cookie = mvc.perform(post("/api/auth/refresh").cookie(new Cookie("livenote_refresh", "old")))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.token").value("access2"))
                .andReturn().getResponse().getHeader(HttpHeaders.SET_COOKIE);

        assertThat(cookie).startsWith("livenote_refresh=new");
    }

    @Test
    void refresh_withoutValidCookie_returns401AndClearsCookie() throws Exception {
        when(refreshTokenService.rotate(null)).thenReturn(Optional.empty());

        String cookie = mvc.perform(post("/api/auth/refresh"))
                .andExpect(status().isUnauthorized())
                .andReturn().getResponse().getHeader(HttpHeaders.SET_COOKIE);

        assertThat(cookie).startsWith("livenote_refresh=;").contains("Max-Age=0");
        verifyNoInteractions(jwtTokenProvider);
    }

    @Test
    void logout_revokesTokenAndClearsCookie() throws Exception {
        String cookie = mvc.perform(post("/api/auth/logout").cookie(new Cookie("livenote_refresh", "old")))
                .andExpect(status().isOk())
                .andReturn().getResponse().getHeader(HttpHeaders.SET_COOKIE);

        verify(refreshTokenService).revoke("old");
        assertThat(cookie).contains("Max-Age=0");
    }
}
