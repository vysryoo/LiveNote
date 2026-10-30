package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.entity.SummaryPhase;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.messaging.simp.SimpMessagingTemplate;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

/**
 * 브라우저로 보내는 STOMP 메시지의 토픽 주소와 내용을 고정한다. 프론트엔드가 이 형식으로 메시지를 읽으므로 바뀌면 안 된다.
 */
@ExtendWith(MockitoExtension.class)
class StreamGatewayTest {

    @Mock SimpMessagingTemplate template;

    private StreamGateway gateway;

    @BeforeEach
    void setUp() {
        gateway = new StreamGateway(template);
    }

    @Test
    void transcript() {
        gateway.sendTranscript(1L, new TranscriptResponseDto(5L, 1L, 2, 30, 34, "전사"), true);

        verify(template).convertAndSend("/topic/lectures.1.transcripts", (Object) Map.of(
                "type", "transcript", "lectureId", 1L, "sectionIndex", 2,
                "startSec", 30, "endSec", 34, "text", "전사", "isFinal", true));
    }

    @Test
    void summary_sentToSectionAndLectureTopics() {
        Summary summary = Summary.builder().lectureId(1L).sectionIndex(2).text("요약").phase(SummaryPhase.PARTIAL).build();

        gateway.sendSummary(summary);

        Map<String, Object> expected = Map.of(
                "type", "summary", "lectureId", 1L, "sectionIndex", 2, "text", "요약", "phase", "partial");
        verify(template).convertAndSend("/topic/lectures.1.summary.2", (Object) expected);
        verify(template).convertAndSend("/topic/lectures.1.summary", (Object) expected);
    }

    @Test
    void resourcesAndQnaLists() {
        List<ResourceResponseDto> resources = List.of(new ResourceResponseDto());
        List<QnaResponseDto> qna = List.of(new QnaResponseDto());

        gateway.sendResources(1L, 2, resources);
        gateway.sendQna(1L, 2, qna);

        verify(template).convertAndSend("/topic/lectures.1.resources", (Object) Map.of(
                "type", "resources", "lectureId", 1L, "sectionIndex", 2, "items", resources));
        verify(template).convertAndSend("/topic/lectures.1.qna", (Object) Map.of(
                "type", "qna", "lectureId", 1L, "sectionIndex", 2, "items", qna));
    }

    @Test
    void error() {
        gateway.sendError(1L, "실패");

        verify(template).convertAndSend("/topic/lectures.1.error", (Object) Map.of("type", "error", "message", "실패"));
    }

    @Test
    void section() {
        gateway.sendSection(1L, 3);

        Map<String, Object> payload = captureSent("/topic/lectures.1.section");
        assertThat(payload).containsEntry("type", "section").containsEntry("lectureId", 1L)
                .containsEntry("sectionIndex", 3).containsKey("timestamp").hasSize(4);
    }

    @Test
    void streamToken_inProgress() {
        gateway.sendStreamToken(1L, "qna_stream", "qna_1_2_2", "토큰", false, null, "질문", null);

        assertThat(captureSent("/topic/lectures.1.stream")).isEqualTo(Map.of(
                "type", "qna_stream", "cardId", "qna_1_2_2", "isComplete", false, "token", "토큰", "title", "질문"));
    }

    @Test
    void streamToken_complete() {
        Object data = new ResourceResponseDto();

        gateway.sendStreamToken(1L, "resource_stream", "resource_1_2_2", null, true, data, null, null);

        assertThat(captureSent("/topic/lectures.1.stream")).isEqualTo(Map.of(
                "type", "resource_stream", "cardId", "resource_1_2_2", "isComplete", true, "data", data));
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> captureSent(String destination) {
        ArgumentCaptor<Object> payload = ArgumentCaptor.forClass(Object.class);
        verify(template, times(1)).convertAndSend(anyString(), any(Object.class));
        verify(template).convertAndSend(org.mockito.ArgumentMatchers.eq(destination), payload.capture());
        return (Map<String, Object>) payload.getValue();
    }
}
