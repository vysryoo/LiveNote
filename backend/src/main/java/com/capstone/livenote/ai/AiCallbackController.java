package com.capstone.livenote.ai;

import com.capstone.livenote.card.ResourceCallbackService;
import com.capstone.livenote.summary.SummaryCallbackService;
import com.capstone.livenote.global.ApiResponse;
import com.capstone.livenote.global.security.InternalApiKey;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;
import lombok.extern.slf4j.Slf4j;


// AI 쪽에서 백엔드로 결과 보내기
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/ai/callback")
@Tag(
        name = "AI 콜백 API",
        description = "AI 서버가 백엔드로 요약 / 자료추천 결과를 전달"
)
@Slf4j
public class AiCallbackController {

    private final ResourceCallbackService resourceCallbackService;
    private final SummaryCallbackService summaryCallbackService;
    private final ObjectMapper objectMapper;
    private final InternalApiKey internalApiKey;

    @Operation(
            summary = "AI 서버가 결과를 백엔드에 전달"
    )
    @PostMapping
    public ApiResponse<Void> handleCallback(
            @RequestParam String type,
            @RequestBody Map<String, Object> payload,
            @RequestHeader(value = InternalApiKey.HEADER, required = false) String apiKey
    ) {
        // 로그인 토큰이 없는 서버 간 요청이라 인증 필터 대신 공유 키로 AI 서버인지 확인
        if (!internalApiKey.matches(apiKey)) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "invalid internal api key");
        }
        log.info("AI callback received type={}, keys={}", type, payload.keySet());
        switch (type) {

            case "resources" -> {
                ResourceCallbackDto dto = new ObjectMapper().convertValue(payload, ResourceCallbackDto.class);
                resourceCallbackService.handleResourceCallback(dto);
            }

            case "summary" -> {
                SummaryCallbackDto dto = objectMapper.convertValue(payload, SummaryCallbackDto.class);
                summaryCallbackService.handleSummaryCallback(dto);
            }

            default -> throw new IllegalArgumentException("Unsupported callback type: " + type);
        }

        return ApiResponse.ok();
    }
}
