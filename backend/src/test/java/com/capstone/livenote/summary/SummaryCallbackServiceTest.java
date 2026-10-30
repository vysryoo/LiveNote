package com.capstone.livenote.summary;

import com.capstone.livenote.card.CardRequestService;
import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.ai.AiAutoCardProperties;
import com.capstone.livenote.ai.SummaryCallbackDto;
import com.capstone.livenote.global.stomp.StreamGateway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class SummaryCallbackServiceTest {

    @Mock SummaryService summaryService;
    @Mock StreamGateway streamGateway;
    @Mock CardRequestService cardRequestService;
    @Mock AiServerClient aiServerClient;
    @Spy AiAutoCardProperties autoCardProperties = new AiAutoCardProperties();

    @InjectMocks
    SummaryCallbackService service;

    private SummaryCallbackDto partial() {
        return SummaryCallbackDto.builder()
                .lectureId(1L)
                .sectionIndex(0)
                .text("스택은 후입선출 구조이다.")
                .phase("PARTIAL")
                .status("COMPLETED")
                .build();
    }

    @Test
    void partialSummary_sendsSummaryAndStartsAutoCards() {
        service.handleSummaryCallback(partial());

        verify(streamGateway).sendSummary(any(Summary.class));
        verify(cardRequestService).startAutoCards(1L, 0, "스택은 후입선출 구조이다.");
    }

    @Test
    void partialSummary_autoCardsDisabled_sendsSummaryWithoutCardRequests() {
        autoCardProperties.setEnabled(false);

        service.handleSummaryCallback(partial());

        verify(streamGateway).sendSummary(any(Summary.class));
        verifyNoInteractions(cardRequestService);
    }
}
