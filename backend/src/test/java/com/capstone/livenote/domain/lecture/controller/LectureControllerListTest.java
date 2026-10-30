package com.capstone.livenote.domain.lecture.controller;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.service.LectureService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@ExtendWith(MockitoExtension.class)
class LectureControllerListTest {

    @Mock LectureService lectureService;
    @Mock RagClient ragClient;

    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        mvc = MockMvcBuilders.standaloneSetup(new LectureController(lectureService, ragClient))
                .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
                .build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(7L, null, Collections.emptyList()));
    }

    @AfterEach
    void clearSecurity() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void list_returnsPageWithTotalAndHasNext() throws Exception {
        List<Lecture> lectures = List.of(Lecture.builder().id(1L).userId(7L).title("a").status(Lecture.Status.RECORDING).build(),
                Lecture.builder().id(2L).userId(7L).title("b").status(Lecture.Status.RECORDING).build());
        when(lectureService.list(eq(7L), any())).thenReturn(new PageImpl<>(lectures, PageRequest.of(1, 2), 25));

        mvc.perform(get("/api/lectures").param("page", "1").param("size", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.items.length()").value(2))
                .andExpect(jsonPath("$.data.items[0].id").value(1))
                .andExpect(jsonPath("$.data.total").value(25))
                .andExpect(jsonPath("$.data.hasNext").value(true));
    }

    @Test
    void list_defaultsToFirstPageOf20AndLimitsSize() throws Exception {
        when(lectureService.list(eq(7L), any())).thenReturn(new PageImpl<>(List.of()));
        ArgumentCaptor<Pageable> pageable = ArgumentCaptor.forClass(Pageable.class);

        mvc.perform(get("/api/lectures")).andExpect(status().isOk());
        mvc.perform(get("/api/lectures").param("page", "-3").param("size", "5000")).andExpect(status().isOk());

        verify(lectureService, times(2)).list(eq(7L), pageable.capture());
        assertThat(pageable.getAllValues().get(0)).isEqualTo(PageRequest.of(0, 20));
        assertThat(pageable.getAllValues().get(1)).isEqualTo(PageRequest.of(0, 100));
    }
}
