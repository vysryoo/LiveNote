package com.capstone.livenote.card;

import com.capstone.livenote.lecture.LectureService;
import com.capstone.livenote.global.GlobalExceptionHandler;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class CardControllerTest {

    @Mock CardRequestService cardRequestService;
    @Mock LectureService lectureService;

    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        mvc = MockMvcBuilders.standaloneSetup(new CardController(cardRequestService, lectureService))
                .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(7L, null, Collections.emptyList()));
    }

    @AfterEach
    void clearSecurity() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void startQnaStream_acceptsCardIndexAndAnswersEmptyData() throws Exception {
        // 프론트엔드는 응답 본문에 data 키가 있어야 정상 응답으로 처리함
        mvc.perform(post("/api/start-qna-stream")
                        .param("lectureId", "4").param("sectionIndex", "1")
                        .param("cardIndex", "2").param("qnaType", "concept"))
                .andExpect(status().isOk())
                .andExpect(content().json("{\"ok\":true,\"data\":null,\"message\":null}", true));

        verify(lectureService).getOwned(4L, 7L);
        verify(cardRequestService).requestExtraQna(4L, 1, "concept");
    }

    @Test
    void startResourcesStream_rejectsOtherUsersLecture() throws Exception {
        when(lectureService.getOwned(4L, 7L)).thenThrow(new EntityNotFoundException("lecture"));

        mvc.perform(post("/api/start-resources-stream")
                        .param("lectureId", "4").param("sectionIndex", "1")
                        .param("cardIndex", "2").param("resourceType", "paper"))
                .andExpect(status().isNotFound());

        verifyNoInteractions(cardRequestService);
    }
}
