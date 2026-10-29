package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import com.capstone.livenote.domain.transcript.service.RecordingStateStore;
import com.capstone.livenote.domain.transcript.service.RecordingStateStore.SectionState;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InOrder;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class SectionAggregationServiceTest {

    private static final long LECTURE = 1L;

    @Mock RagClient ragClient;
    @Mock TranscriptRepository transcriptRepository;
    @Mock RecordingStateStore stateStore;
    @Mock StreamGateway streamGateway;

    private SectionAggregationService service;
    private SectionState storedState;
    private final List<Transcript> transcripts = new ArrayList<>();

    @BeforeEach
    void setUp() {
        service = new SectionAggregationService(ragClient, transcriptRepository, stateStore, streamGateway);

        when(stateStore.findSection(LECTURE)).thenAnswer(inv -> Optional.ofNullable(storedState));
        doAnswer(inv -> {
            storedState = inv.getArgument(1);
            return null;
        }).when(stateStore).saveSection(eq(LECTURE), any());

        when(transcriptRepository.findMaxSectionIndexByLectureId(LECTURE)).thenAnswer(inv ->
                transcripts.stream().map(Transcript::getSectionIndex).max(Integer::compare).orElse(null));
        when(transcriptRepository.findByLectureIdAndSectionIndexOrderByStartSecAsc(eq(LECTURE), anyInt()))
                .thenAnswer(inv -> transcripts.stream()
                        .filter(t -> t.getSectionIndex().equals(inv.getArgument(1)))
                        .toList());
    }

    // TranscriptService.saveFromStt와 같은 순서로 섹션 배정, 저장, 요약 확인을 수행
    private int receive(int startSec, int endSec, String text) {
        int sectionIndex = service.assignSection(LECTURE, startSec, endSec);
        transcripts.add(Transcript.builder()
                .lectureId(LECTURE).sectionIndex(sectionIndex)
                .startSec(startSec).endSec(endSec).text(text)
                .build());
        service.onTranscriptSaved(LECTURE);
        return sectionIndex;
    }

    private void verifySummary(String phase, int sectionIndex, int startSec, int endSec, String text) {
        verify(ragClient).requestSummaryGeneration(
                eq(LECTURE), isNull(), eq(sectionIndex), eq(startSec), eq(endSec), eq(phase), eq(text));
    }

    @Test
    void firstTranscript_startsSectionZero() {
        assertThat(receive(0, 7, "a")).isZero();

        verify(streamGateway).sendSection(LECTURE, 0);
        verifyNoInteractions(ragClient);
    }

    @Test
    void reaching15Seconds_requestsPartialOnce() {
        receive(0, 7, "a");
        receive(7, 17, "b");
        receive(17, 25, "c");

        verifySummary("PARTIAL", 0, 0, 17, "a b");
        verify(ragClient, times(1)).requestSummaryGeneration(
                anyLong(), any(), anyInt(), anyInt(), anyInt(), eq("PARTIAL"), anyString());
    }

    @Test
    void reaching30Seconds_requestsFinalAndAnnouncesNextSection() {
        receive(0, 7, "a");
        receive(7, 17, "b");
        receive(17, 27, "c");
        receive(27, 35, "d");

        verifySummary("FINAL", 0, 0, 35, "a b c d");
        InOrder order = inOrder(streamGateway);
        order.verify(streamGateway).sendSection(LECTURE, 0);
        order.verify(streamGateway).sendSection(LECTURE, 1);
    }

    @Test
    void transcriptAfterFinal_goesToNextSection() {
        receive(0, 17, "a");
        receive(17, 35, "b");

        assertThat(receive(35, 44, "c")).isEqualTo(1);
        assertThat(storedState.startSec()).isEqualTo(35);
        verify(streamGateway, times(1)).sendSection(LECTURE, 1);
    }

    @Test
    void sectionClosedByGap_sendsFinalBeforeMovingOn() {
        receive(0, 20, "a");

        // 섹션 시작 후 30초가 지나 들어온 전사. 이전 섹션은 30초를 채우지 못해 최종 요약이 없었음
        assertThat(receive(40, 45, "b")).isEqualTo(1);

        verifySummary("FINAL", 0, 0, 20, "a");
        verify(streamGateway).sendSection(LECTURE, 1);
    }

    @Test
    void missingState_resumesFromLastSectionInDb() {
        transcripts.add(Transcript.builder().lectureId(LECTURE).sectionIndex(0).startSec(0).endSec(35).text("a").build());
        transcripts.add(Transcript.builder().lectureId(LECTURE).sectionIndex(1).startSec(35).endSec(52).text("b").build());

        assertThat(receive(52, 58, "c")).isEqualTo(1);

        assertThat(storedState).isEqualTo(new SectionState(1, 35, 58, true, false));
        verify(streamGateway, never()).sendSection(anyLong(), anyInt());
        verifyNoInteractions(ragClient);
    }

    @Test
    void missingState_afterFinishedSection_startsNextSection() {
        transcripts.add(Transcript.builder().lectureId(LECTURE).sectionIndex(2).startSec(60).endSec(92).text("a").build());

        assertThat(receive(92, 99, "b")).isEqualTo(3);
        verifyNoInteractions(ragClient);
    }
}
