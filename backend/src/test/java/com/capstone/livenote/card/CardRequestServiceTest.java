package com.capstone.livenote.card;

import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.ai.AiHistoryProperties;
import com.capstone.livenote.ai.AiRequestPayloads;
import com.capstone.livenote.global.stomp.StreamGateway;
import com.capstone.livenote.lecture.Lecture;
import com.capstone.livenote.lecture.LectureService;
import com.capstone.livenote.summary.Summary;
import com.capstone.livenote.summary.SummaryService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CardRequestServiceTest {

    @Mock AiServerClient aiServerClient;
    @Mock SummaryService summaryService;
    @Mock ResourceRepository resourceRepository;
    @Mock QnaRepository qnaRepository;
    @Mock LectureService lectureService;
    @Mock StreamGateway streamGateway;
    @Mock QnaStreamService qnaStreamService;

    private final AiHistoryProperties props = new AiHistoryProperties();
    private CardRequestService service;

    @BeforeEach
    void setUp() {
        service = new CardRequestService(aiServerClient, summaryService, resourceRepository, qnaRepository,
                lectureService, props, streamGateway, qnaStreamService);
    }

    @Test
    void requestExtraResource_buildsPreviousAndExcludes() {
        props.setPreviousSummaryCount(2);
        props.setPreviousResourceSections(2);

        Summary current = Summary.builder()
                .id(10L).lectureId(1L).sectionIndex(3).text("current summary").build();
        when(summaryService.findByLectureAndSection(1L, 3)).thenReturn(Optional.of(current));
        when(summaryService.findPreviousSummaries(1L, 3, 2)).thenReturn(List.of(
                Summary.builder().sectionIndex(2).text("prev2").build(),
                Summary.builder().sectionIndex(1).text("prev1").build()
        ));
        when(resourceRepository.findByLectureIdAndSectionIndexBetweenOrderByIdAsc(1L, 1, 2)).thenReturn(List.of(
                Resource.builder().type(Resource.Type.VIDEO).title("old video").build(),
                Resource.builder().type(Resource.Type.WIKI).title("old wiki").build(),
                Resource.builder().type(Resource.Type.PAPER).url("doi/123").build(),
                Resource.builder().type(Resource.Type.GOOGLE).url("http://example.com").build()
        ));

        service.requestExtraResource(1L, 3, "paper");

        ArgumentCaptor<AiRequestPayloads.ResourceRecommendPayload> captor =
                ArgumentCaptor.forClass(AiRequestPayloads.ResourceRecommendPayload.class);
        verify(aiServerClient).requestResourceRecommendation(captor.capture(), eq(List.of("PAPER")));
        var payload = captor.getValue();

        assertThat(payload.getPreviousSummaries()).hasSize(2);
        assertThat(payload.getYtExclude()).containsExactly("old video");
        assertThat(payload.getWikiExclude()).containsExactly("old wiki");
        assertThat(payload.getPaperExclude()).containsExactly("doi/123");
        assertThat(payload.getGoogleExclude()).containsExactly("http://example.com");
        assertThat(payload.getSectionSummary()).isEqualTo("current summary");
        assertThat(payload.getSummaryId()).isEqualTo(10L);
    }

    @Test
    void requestExtraQna_usesSubjectAndPreviousQa() {
        props.setPreviousQaSections(2);

        Summary current = Summary.builder()
                .id(20L).lectureId(7L).sectionIndex(4).text("current summary").build();
        when(summaryService.findByLectureAndSection(7L, 4)).thenReturn(Optional.of(current));
        when(lectureService.get(7L)).thenReturn(Lecture.builder().id(7L).subject("math").build());
        when(qnaRepository.findByLectureIdAndSectionIndexBetweenOrderBySectionIndexAsc(7L, 2, 3)).thenReturn(List.of(
                Qna.builder().type(Qna.Type.CONCEPT).question("q1").answer("a1").build(),
                Qna.builder().type(Qna.Type.COMPARISON).question("q2").answer("a2").build()
        ));

        service.requestExtraQna(7L, 4, "concept");

        ArgumentCaptor<AiRequestPayloads.QnaGeneratePayload> captor =
                ArgumentCaptor.forClass(AiRequestPayloads.QnaGeneratePayload.class);
        verify(qnaStreamService).generate(captor.capture(), eq(List.of("CONCEPT")));
        var payload = captor.getValue();

        assertThat(payload.getSubject()).isEqualTo("math");
        assertThat(payload.getPreviousQa()).extracting(AiRequestPayloads.PreviousQaPayload::getType)
                .containsExactly("concept", "comparison");
        assertThat(payload.getSectionSummary()).isEqualTo("current summary");
    }

    @Test
    void requestExtraQna_sectionFull_resendsCurrentCardsWithoutGenerating() {
        List<Qna> full = List.of(qna(1L), qna(2L), qna(3L));
        when(qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(7L, 4)).thenReturn(full);

        service.requestExtraQna(7L, 4, "concept");

        verify(streamGateway).sendQna(eq(7L), eq(4), argThat(items -> items.size() == 3));
        verifyNoInteractions(qnaStreamService, summaryService);
    }

    @Test
    void startAutoCards_requestsTwoResourceAndTwoQnaTypes() {
        when(lectureService.get(7L)).thenReturn(Lecture.builder().id(7L).build());

        service.startAutoCards(7L, 0, "스택과 큐의 차이를 설명한다.");

        verify(aiServerClient).requestResourceRecommendation(
                argThat(payload -> payload.getSummaryId() == null), eq(List.of("WIKI", "BLOG")));
        verify(qnaStreamService).generate(any(), eq(List.of("CONCEPT", "APPLICATION")));
    }

    @Test
    void startAutoCards_resourceFailureDoesNotSkipQna() {
        when(lectureService.get(7L)).thenReturn(Lecture.builder().id(7L).build());
        doThrow(WebClientResponseException.create(400, "Bad Request", null, null, null))
                .when(aiServerClient).requestResourceRecommendation(any(), any());

        assertThatCode(() -> service.startAutoCards(7L, 0, "요약")).doesNotThrowAnyException();

        verify(qnaStreamService).generate(any(), eq(List.of("CONCEPT", "APPLICATION")));
    }

    @Test
    void startAutoCards_qnaFailureDoesNotFail() {
        when(lectureService.get(7L)).thenThrow(new IllegalStateException("lecture missing"));

        assertThatCode(() -> service.startAutoCards(7L, 0, "요약")).doesNotThrowAnyException();

        verify(aiServerClient).requestResourceRecommendation(any(), eq(List.of("WIKI", "BLOG")));
    }

    private static Qna qna(Long id) {
        return Qna.builder().id(id).lectureId(7L).sectionIndex(4).cardId("qna_7_4_" + (id + 1))
                .type(Qna.Type.CONCEPT).question("q").answer("a").build();
    }
}
