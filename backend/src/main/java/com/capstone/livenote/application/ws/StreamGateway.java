package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class StreamGateway {
    private final SimpMessagingTemplate tmpl;

    // 실시간 전사 전송
    public void sendTranscript(Long lectureId, TranscriptResponseDto dto, boolean isFinal) {
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/transcripts",
                Map.of(
                        "type", "transcript",
                        "lectureId", lectureId,
                        "sectionIndex", dto.getSectionIndex(),
                        "startSec", dto.getStartSec(),
                        "endSec", dto.getEndSec(),
                        "text", dto.getText(),
                        "isFinal", isFinal
                ));
    }

    // summary 실시간 전송
    public void sendSummary(Long lectureId,
                            Integer sectionIndex,
                            String text,
                            String phase) {

        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/summary",
                Map.of(
                        "type", "summary",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "phase", phase,
                        "text", text
                ));
    }


    // resource 실시간 전송
    public void sendResources(Long lectureId, Integer sectionIndex, List<ResourceResponseDto> items) {
        tmpl.convertAndSend(
                "/topic/lectures/" + lectureId + "/resources",
                Map.of(
                        "type", "resources",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }


    // qna 실시간 전송
    public void sendQna(Long lectureId, Integer sectionIndex, List<QnaResponseDto> items) {
        tmpl.convertAndSend(
                "/topic/lectures/" + lectureId + "/qna",
                Map.of(
                        "type", "qna",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }

    // error 전송
    public void sendError(Long lectureId, String error) {
        tmpl.convertAndSend("/topic/lectures/" + lectureId + "/error",
                Map.of("type", "error", "message", error));
    }
}

