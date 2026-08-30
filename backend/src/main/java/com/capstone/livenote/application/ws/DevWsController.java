package com.capstone.livenote.application.ws;

import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

// 임시테스트용
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/dev/ws")
public class DevWsController {
    private final StreamGateway streamGateway;

    // 1) 전사 메시지 테스트
    @PostMapping("/lectures/{lectureId}/transcript")
    public ApiResponse<Void> pushTranscript(@PathVariable Long lectureId) {
        var dto = new TranscriptResponseDto(999L, lectureId, 3, 90, 120, "테스트 전사입니다.");
        streamGateway.sendTranscript(lectureId, dto, true);
        return ApiResponse.ok();
    }

    // 2) 요약/리소스/QnA도 필요하면 비슷하게
    @PostMapping("/lectures/{lectureId}/summary")
    public ApiResponse<Void> pushSummary(@PathVariable Long lectureId) {
        streamGateway.sendSummary(
                lectureId,
                3,                        // sectionIndex (테스트용)
                "테스트 요약입니다.",        // text
                "FINAL"                  // phase: "PARTIAL" or "FINAL"
        );
        return ApiResponse.ok();
    }
}
