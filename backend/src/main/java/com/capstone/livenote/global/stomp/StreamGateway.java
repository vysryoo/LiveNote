package com.capstone.livenote.global.stomp;

import com.capstone.livenote.card.QnaResponseDto;
import com.capstone.livenote.card.ResourceResponseDto;
import com.capstone.livenote.summary.Summary;
import com.capstone.livenote.recording.TranscriptResponseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 강의별 STOMP 토픽 {@code /topic/lectures.{lectureId}.{name}}으로 실시간 메시지를 보낸다.
 *
 * 메시지는 RabbitMQ를 거쳐 그 강의를 구독한 모든 브라우저에 전달된다.
 */
@Component
@RequiredArgsConstructor
public class StreamGateway {
    private final SimpMessagingTemplate tmpl;

    // RabbitMQ STOMP는 /topic/ 뒤에 '/'를 허용하지 않아 '.'으로 구분함
    private static String lectureTopic(Long lectureId, String name) {
        return "/topic/lectures." + lectureId + "." + name;
    }

    /**
     * 전사 한 문장을 {@code transcripts} 토픽으로 보낸다.
     *
     * @param lectureId 강의 ID
     * @param dto 저장한 전사
     * @param isFinal 확정된 문장인지 여부
     */
    public void sendTranscript(Long lectureId, TranscriptResponseDto dto, boolean isFinal) {
        tmpl.convertAndSend(lectureTopic(lectureId, "transcripts"),
                Map.of(
                        "type", "transcript",
                        "lectureId", lectureId,
                        "sectionIndex", dto.sectionIndex(),
                        "startSec", dto.startSec(),
                        "endSec", dto.endSec(),
                        "text", dto.text(),
                        "isFinal", isFinal
                ));
    }

    /**
     * 요약을 전송한다.
     *
     * @param summary 요약. 부분 요약은 저장하지 않아 ID가 없을 수 있음
     */
    public void sendSummary(Summary summary) {
        tmpl.convertAndSend(lectureTopic(summary.getLectureId(), "summary"), Map.of(
                "type", "summary",
                "lectureId", summary.getLectureId(),
                "sectionIndex", summary.getSectionIndex(),
                "text", summary.getText() != null ? summary.getText() : "",
                "phase", summary.getPhase() != null ? summary.getPhase().name().toLowerCase() : "final"
        ));
    }

    /**
     * 섹션의 자료 카드 전체 목록을 {@code resources} 토픽으로 보낸다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param items 섹션의 자료 카드 전체
     */
    public void sendResources(Long lectureId, Integer sectionIndex, List<ResourceResponseDto> items) {
        tmpl.convertAndSend(
                lectureTopic(lectureId, "resources"),
                Map.of(
                        "type", "resources",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }


    /**
     * 섹션의 QnA 카드 전체 목록을 {@code qna} 토픽으로 보낸다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param items 섹션의 QnA 카드 전체
     */
    public void sendQna(Long lectureId, Integer sectionIndex, List<QnaResponseDto> items) {
        tmpl.convertAndSend(
                lectureTopic(lectureId, "qna"),
                Map.of(
                        "type", "qna",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "items", items
                )
        );
    }

    /**
     * 오류 메시지를 {@code error} 토픽으로 보낸다.
     *
     * @param lectureId 강의 ID
     * @param error 화면에 보낼 오류 메시지
     */
    public void sendError(Long lectureId, String error) {
        tmpl.convertAndSend(lectureTopic(lectureId, "error"),
                Map.of("type", "error", "message", error));
    }

    /**
     * 다음 전사부터 속할 섹션 번호를 {@code section} 토픽으로 알린다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 새 섹션 번호
     */
    public void sendSection(Long lectureId, int sectionIndex) {
        tmpl.convertAndSend(
                lectureTopic(lectureId, "section"),
                Map.of(
                        "type", "section",
                        "lectureId", lectureId,
                        "sectionIndex", sectionIndex,
                        "timestamp", System.currentTimeMillis()
                )
        );
    }

    /**
     * 생성 중인 카드에 새로 생긴 글자 조각을 전송한다.
     *
     * @param lectureId 강의 ID
     * @param type 카드 종류. {@code qna_stream} 또는 {@code resource_stream}
     * @param cardId 카드 ID
     * @param token 새로 생긴 글자 조각
     * @param title 카드 제목. QnA는 질문. 없으면 null이며 메시지에서 빠짐
     */
    public void sendStreamToken(Long lectureId, String type, String cardId, String token, String title) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", type);
        payload.put("cardId", cardId);
        payload.put("isComplete", false);
        payload.put("token", token);
        if (title != null) {
            payload.put("title", title);
        }
        tmpl.convertAndSend(lectureTopic(lectureId, "stream"), payload);
    }

    /**
     * 생성이 끝난 카드를 전송한다.
     *
     * @param lectureId 강의 ID
     * @param type 카드 종류. {@code qna_stream} 또는 {@code resource_stream}
     * @param cardId 카드 ID
     * @param data 저장된 카드
     */
    public void sendStreamComplete(Long lectureId, String type, String cardId, Object data) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", type);
        payload.put("cardId", cardId);
        payload.put("isComplete", true);
        payload.put("data", data);
        tmpl.convertAndSend(lectureTopic(lectureId, "stream"), payload);
    }
}
