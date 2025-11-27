//package com.capstone.livenote.application.ai.service;
//
//import com.capstone.livenote.application.ai.client.RagClient;
//import com.capstone.livenote.application.openai.service.OpenAiSummaryService;
//import com.capstone.livenote.domain.summary.entity.Summary;
//import com.capstone.livenote.domain.summary.service.SummaryService;
//import org.junit.jupiter.api.BeforeEach;
//import org.junit.jupiter.api.Test;
//import org.mockito.ArgumentCaptor;
//
//import static org.assertj.core.api.Assertions.assertThat;
//import static org.mockito.ArgumentMatchers.any;
//import static org.mockito.Mockito.*;
//
//class SectionAggregationServiceTest {
//
//    private OpenAiSummaryService openAiSummaryService;
//    private SummaryService summaryService;
//    private RagClient ragClient;
//    private AiRequestService aiRequestService;
//    private SectionAggregationService service;
//
//    @BeforeEach
//    void setUp() {
//        openAiSummaryService = mock(OpenAiSummaryService.class);
//        summaryService = mock(SummaryService.class);
//        ragClient = mock(RagClient.class);
//        aiRequestService = mock(AiRequestService.class);
//
//        service = new SectionAggregationService(openAiSummaryService, summaryService, ragClient, aiRequestService);
//    }
//
//    @Test
//    void triggersPartialAndFinalFlowWithUpsert() {
//        when(openAiSummaryService.summarize(any()))
//                .thenReturn("partial summary")
//                .thenReturn("final summary");
//
//        Summary saved = Summary.builder()
//                .id(10L)
//                .lectureId(1L)
//                .sectionIndex(0)
//                .startSec(0)
//                .endSec(30)
//                .text("final summary")
//                .build();
//        when(summaryService.createSectionSummary(eq(1L), eq(0), any())).thenReturn(saved);
//
//        // 누적 30초가 될 때까지 전사를 쌓는다.
//        service.onNewTranscript(1L, 0, 10, "chunk1");
//        service.onNewTranscript(1L, 10, 20, "chunk2"); // partial 트리거
//        service.onNewTranscript(1L, 20, 30, "chunk3"); // final 트리거
//
//        verify(aiRequestService, times(1))
//                .requestResourcesWithSummary(1L, null, 0, "partial summary");
//        verify(aiRequestService, times(1))
//                .requestQnaWithSummary(1L, null, 0, "partial summary");
//
//        ArgumentCaptor<String> summaryTextCaptor = ArgumentCaptor.forClass(String.class);
//        verify(summaryService).createSectionSummary(eq(1L), eq(0), summaryTextCaptor.capture());
//        assertThat(summaryTextCaptor.getValue()).isEqualTo("final summary");
//
//        verify(ragClient).upsertSummaryText(1L, saved);
//    }
//}
