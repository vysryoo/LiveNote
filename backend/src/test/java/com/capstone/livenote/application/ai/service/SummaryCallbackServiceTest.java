package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.AiServerClient;
import com.capstone.livenote.application.ai.config.AiAutoCardProperties;
import com.capstone.livenote.application.ai.dto.SummaryCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.service.SummaryService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SummaryCallbackServiceTest {

    @Mock SummaryService summaryService;
    @Mock StreamGateway streamGateway;
    @Mock AiRequestService aiRequestService;
    @Mock AiServerClient aiServerClient;
    @Spy AiAutoCardProperties autoCardProperties = new AiAutoCardProperties();

    @InjectMocks
    SummaryCallbackService service;

    private SummaryCallbackDto partial() {
        SummaryCallbackDto dto = new SummaryCallbackDto();
        dto.setLectureId(1L);
        dto.setSectionIndex(0);
        dto.setText("스택은 후입선출 구조이다.");
        dto.setPhase("PARTIAL");
        dto.setStatus("COMPLETED");
        return dto;
    }

    @Test
    void partialSummary_resourceRequestFailureDoesNotFailCallbackOrSkipQna() {
        doThrow(WebClientResponseException.create(400, "Bad Request", null, null, null))
                .when(aiRequestService).requestResourcesWithSummary(anyLong(), isNull(), anyInt(), anyString(), eq(2));

        assertThatCode(() -> service.handleSummaryCallback(partial())).doesNotThrowAnyException();

        verify(streamGateway).sendSummary(any(Summary.class));
        verify(aiRequestService).requestQnaWithSummary(eq(1L), isNull(), eq(0), anyString(), eq(2));
    }

    @Test
    void partialSummary_qnaRequestFailureDoesNotFailCallback() {
        doThrow(new IllegalStateException("lecture missing"))
                .when(aiRequestService).requestQnaWithSummary(anyLong(), isNull(), anyInt(), anyString(), eq(2));

        assertThatCode(() -> service.handleSummaryCallback(partial())).doesNotThrowAnyException();

        verify(aiRequestService).requestResourcesWithSummary(eq(1L), isNull(), eq(0), anyString(), eq(2));
    }

    @Test
    void partialSummary_autoCardsDisabled_sendsSummaryWithoutCardRequests() {
        autoCardProperties.setEnabled(false);

        service.handleSummaryCallback(partial());

        verify(streamGateway).sendSummary(any(Summary.class));
        verifyNoInteractions(aiRequestService);
    }
}
