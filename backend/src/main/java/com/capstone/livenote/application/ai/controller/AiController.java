package com.capstone.livenote.application.ai.controller;

import com.capstone.livenote.application.ai.service.AiRequestService;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Tag(name = "AI & Cards API", description = "분할 화면 추가 카드 스트리밍")
public class AiController {

    private final AiRequestService aiRequestService;
    private final LectureService lectureService;

    // 다른 사용자의 강의로 AI 생성을 요청하지 못하도록 소유자를 확인. 아니면 404
    private void requireOwnedLecture(Long lectureId) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "not authenticated");
        }
        Long userId;
        try {
            userId = Long.parseLong(authentication.getName());
        } catch (NumberFormatException e) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "invalid user id");
        }
        lectureService.getOwned(lectureId, userId);
    }

    // QnA 스트리밍
    @Operation(summary = "QnA 확장 카드 스트리밍 시작")
    @PostMapping("/start-qna-stream")
    public ApiResponse<Map<String, Object>> startQnaStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String qnaType
    ) {
        requireOwnedLecture(lectureId);
        aiRequestService.requestQnaWithType(lectureId, sectionIndex, qnaType);
        String cardId = "qna_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "qna"));
    }

    // Resource 스트리밍
    @Operation(summary = "Resource 확장 카드 스트리밍 시작")
    @PostMapping("/start-resources-stream")
    public ApiResponse<Map<String, Object>> startResourceStream(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam Integer cardIndex,
            @RequestParam String resourceType
    ) {
        requireOwnedLecture(lectureId);
        aiRequestService.requestResourcesWithType(lectureId, sectionIndex, resourceType);
        String cardId = "res_" + lectureId + "_" + sectionIndex + "_" + cardIndex;
        return ApiResponse.ok(Map.of("success", true, "cardId", cardId, "type", "resource_stream"));
    }
}
