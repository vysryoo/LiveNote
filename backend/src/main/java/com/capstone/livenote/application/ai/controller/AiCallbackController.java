package com.capstone.livenote.application.ai.controller;


import com.capstone.livenote.application.ai.dto.AiCallbackDto;
import com.capstone.livenote.application.ai.service.AiCallbackService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai")
public class AiCallbackController {
    private final AiCallbackService svc;

    @PostMapping("/callback")
    public ApiResponse<Void> callback(@RequestBody AiCallbackDto payload){
        svc.apply(payload);
        return ApiResponse.ok();
    }

//    @PostMapping("/ai/callback/transcript")
//    public ApiResponse<Void> saveTranscript(@RequestBody TranscriptCallbackDto dto){
//        transcriptService.saveFromStt(dto.getLectureId(), dto.getStartSec(), dto.getEndSec(), dto.getText());
//        return ApiResponse.ok();
//    }

}