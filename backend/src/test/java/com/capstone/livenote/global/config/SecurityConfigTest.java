package com.capstone.livenote.global.config;

import com.capstone.livenote.global.security.JwtTokenProvider;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class SecurityConfigTest {

    @Autowired
    MockMvc mvc;

    @Autowired
    JwtTokenProvider jwtTokenProvider;

    @Test
    void protectedApi_withoutToken_returns401() throws Exception {
        mvc.perform(get("/api/lectures")).andExpect(status().isUnauthorized());
    }

    @Test
    void protectedApi_withInvalidToken_returns401() throws Exception {
        mvc.perform(get("/api/lectures").header("Authorization", "Bearer invalid.token.value"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void userApi_withoutToken_returns401() throws Exception {
        mvc.perform(get("/api/users/me")).andExpect(status().isUnauthorized());
        mvc.perform(patch("/api/users/me/language")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"language\":\"en\"}"))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void validToken_passesUserIdToController() throws Exception {
        // 사용자 ID가 컨트롤러까지 전달되면 없는 사용자라 404, 전달되지 않으면 null 조회로 500이 됨
        String token = jwtTokenProvider.createToken(Long.MAX_VALUE);

        mvc.perform(get("/api/users/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());
    }
}
