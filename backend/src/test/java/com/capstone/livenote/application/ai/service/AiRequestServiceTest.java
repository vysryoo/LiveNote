package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ai.config.AiHistoryProperties;
import com.capstone.livenote.application.ai.dto.AiRequestPayloads;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.service.SummaryService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AiRequestServiceTest {

    @Mock RagClient ragClient;
    @Mock SummaryService summaryService;
    @Mock ResourceService resourceService;
    @Mock QnaService qnaService;
    @Mock LectureService lectureService;
    @Mock StreamGateway streamGateway;
    @Mock QnaStreamService qnaStreamService;

    @Test
    void requestResourcesWithType_buildsPreviousAndExcludes() {
        AiHistoryProperties props = new AiHistoryProperties();
        props.setPreviousSummaryCount(2);
        props.setPreviousResourceSections(2);

        Summary current = Summary.builder()
                .id(10L).lectureId(1L).sectionIndex(3).text("current summary").build();
        when(summaryService.findByLectureAndSection(1L, 3)).thenReturn(Optional.of(current));
        when(summaryService.findPreviousSummaries(1L, 3, 2)).thenReturn(List.of(
                Summary.builder().sectionIndex(2).text("prev2").build(),
                Summary.builder().sectionIndex(1).text("prev1").build()
        ));
        // 현재 섹션 자료가 3개 미만이어야 추천을 요청함
        when(resourceService.findBySectionRange(1L, 3, 3)).thenReturn(List.of());
        when(resourceService.findBySectionRange(1L, 1, 2)).thenReturn(List.of(
                Resource.builder().type(Resource.Type.VIDEO).title("old video").build(),
                Resource.builder().type(Resource.Type.WIKI).title("old wiki").build(),
                Resource.builder().type(Resource.Type.PAPER).url("doi/123").build(),
                Resource.builder().type(Resource.Type.GOOGLE).url("http://example.com").build()
        ));

        AiRequestService service = new AiRequestService(
                ragClient, summaryService, resourceService, qnaService, lectureService, props, streamGateway, qnaStreamService
        );

        service.requestResourcesWithType(1L, 3, "paper");

        ArgumentCaptor<AiRequestPayloads.ResourceRecommendPayload> captor =
                ArgumentCaptor.forClass(AiRequestPayloads.ResourceRecommendPayload.class);
        verify(ragClient).requestResourceRecommendation(captor.capture(), eq(List.of("PAPER")));
        var payload = captor.getValue();

        assertThat(payload.getPreviousSummaries()).hasSize(2);
        assertThat(payload.getYtExclude()).contains("old video");
        assertThat(payload.getWikiExclude()).contains("old wiki");
        assertThat(payload.getPaperExclude()).contains("doi/123");
        assertThat(payload.getGoogleExclude()).contains("http://example.com");
        assertThat(payload.getSectionSummary()).isEqualTo("current summary");
    }

    @Test
    void requestQnaWithType_usesSubjectAndPreviousQa() {
        AiHistoryProperties props = new AiHistoryProperties();
        props.setPreviousQaSections(2);

        Summary current = Summary.builder()
                .id(20L).lectureId(7L).sectionIndex(4).text("current summary").build();
        when(summaryService.findByLectureAndSection(7L, 4)).thenReturn(Optional.of(current));
        when(lectureService.get(7L)).thenReturn(Lecture.builder().id(7L).subject("math").build());
        when(qnaService.findByLectureWithinSections(7L, 2, 3)).thenReturn(List.of(
                Qna.builder().type(Qna.Type.CONCEPT).question("q1").answer("a1").build(),
                Qna.builder().type(Qna.Type.COMPARISON).question("q2").answer("a2").build()
        ));

        AiRequestService service = new AiRequestService(
                ragClient, summaryService, resourceService, qnaService, lectureService, props, streamGateway, qnaStreamService
        );

        service.requestQnaWithType(7L, 4, "concept");

        ArgumentCaptor<AiRequestPayloads.QnaGeneratePayload> captor =
                ArgumentCaptor.forClass(AiRequestPayloads.QnaGeneratePayload.class);
        verify(qnaStreamService).generate(captor.capture(), eq(List.of("CONCEPT")));
        var payload = captor.getValue();

        assertThat(payload.getSubject()).isEqualTo("math");
        assertThat(payload.getPreviousQa()).hasSize(2);
        assertThat(payload.getSectionSummary()).isEqualTo("current summary");
    }

    @Test
    void requestResourcesWithSummary_partialRequestsWikiAndBlogOnly() {
        AiHistoryProperties props = new AiHistoryProperties();
        AiRequestService service = new AiRequestService(
                ragClient, summaryService, resourceService, qnaService, lectureService, props, streamGateway, qnaStreamService
        );

        service.requestResourcesWithSummary(7L, null, 0, "스택과 큐의 차이를 설명한다.", 2);

        verify(ragClient).requestResourceRecommendation(any(AiRequestPayloads.ResourceRecommendPayload.class), eq(List.of("WIKI", "BLOG")));
    }
}
