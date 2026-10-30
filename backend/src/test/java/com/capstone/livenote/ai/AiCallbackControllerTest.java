package com.capstone.livenote.ai;

import com.capstone.livenote.card.ResourceCallbackService;
import com.capstone.livenote.global.GlobalExceptionHandler;
import com.capstone.livenote.global.security.InternalApiKey;
import com.capstone.livenote.summary.SummaryCallbackService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * AI 서버가 보내는 콜백 본문(키 이름은 ai/server/routes)이 DTO로 바뀌는지 확인한다.
 */
@ExtendWith(MockitoExtension.class)
class AiCallbackControllerTest {

    @Mock ResourceCallbackService resourceCallbackService;
    @Mock SummaryCallbackService summaryCallbackService;

    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        // 운영과 같은 Spring 기본 설정. 모르는 필드는 무시함
        var objectMapper = Jackson2ObjectMapperBuilder.json().build();
        mvc = MockMvcBuilders.standaloneSetup(new AiCallbackController(
                        resourceCallbackService, summaryCallbackService, objectMapper, new InternalApiKey("secret")))
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void summaryCallback_mapsAiServerPayload() throws Exception {
        mvc.perform(post("/api/ai/callback").param("type", "summary")
                        .header(InternalApiKey.HEADER, "secret")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"id":null,"summaryId":null,"lectureId":7,"sectionIndex":2,"startSec":60,"endSec":90,
                                 "text":"요약","phase":"PARTIAL","status":"COMPLETED"}
                                """))
                .andExpect(status().isOk());

        ArgumentCaptor<SummaryCallbackDto> dto = ArgumentCaptor.forClass(SummaryCallbackDto.class);
        verify(summaryCallbackService).handleSummaryCallback(dto.capture());
        assertThat(dto.getValue()).isEqualTo(SummaryCallbackDto.builder()
                .lectureId(7L).sectionIndex(2).startSec(60).endSec(90)
                .text("요약").phase("PARTIAL").status("COMPLETED").build());
    }

    @Test
    void resourceCallback_mapsAiServerPayloadAndIgnoresUnknownFields() throws Exception {
        mvc.perform(post("/api/ai/callback").param("type", "resources")
                        .header(InternalApiKey.HEADER, "secret")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"lectureId":7,"summaryId":null,"sectionIndex":2,"newField":"x",
                                 "resources":[{"type":"wiki","title":"스택","url":"https://w","description":"설명",
                                               "score":0.9,"reason":"이유","detail":{"lang":"ko"}}]}
                                """))
                .andExpect(status().isOk());

        ArgumentCaptor<ResourceCallbackDto> dto = ArgumentCaptor.forClass(ResourceCallbackDto.class);
        verify(resourceCallbackService).handleResourceCallback(dto.capture());
        assertThat(dto.getValue().lectureId()).isEqualTo(7L);
        assertThat(dto.getValue().resources()).containsExactly(ResourceCallbackDto.ResourceItem.builder()
                .type("wiki").title("스택").url("https://w").description("설명")
                .score(0.9).reason("이유").detail(Map.of("lang", "ko")).build());
    }

    @Test
    void callback_withWrongKey_returns401() throws Exception {
        mvc.perform(post("/api/ai/callback").param("type", "summary")
                        .header(InternalApiKey.HEADER, "wrong")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isUnauthorized());

        verifyNoInteractions(summaryCallbackService);
    }
}
