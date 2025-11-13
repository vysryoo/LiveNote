package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.dto.SttChunkRequestDto;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 실시간 STT(음성 전사) 콜백 전용 컨트롤러
 * - 외부 STT 서버가 여기로 POST를 날린다.
 * - TranscriptService.saveFromStt() 를 호출해서
 *   1) Transcript 저장
 *   2) SummaryService 요약 트리거
 *   3) WebSocket 브로드캐스트
 *   를 한 번에 수행
 */
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai/stt")
public class SttCallbackController {

    private final TranscriptService transcriptService;


    @PostMapping("/lectures/{lectureId}/transcript")
    public ApiResponse<Void> ingestTranscript(
            @PathVariable Long lectureId,
            @RequestBody SttChunkRequestDto req
    ) {
        transcriptService.saveFromStt(
                lectureId,
                req.getStartSec(),
                req.getEndSec(),
                req.getText()
        );
        return ApiResponse.ok();
    }
}
