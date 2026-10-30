package com.capstone.livenote.card;

import com.capstone.livenote.lecture.LectureService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;


// 카드 번호는 생성이 시작될 때 서버가 정하므로, 프론트엔드가 함께 보내는 cardIndex는 받지 않음
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Tag(name = "AI & Cards API", description = "분할 화면 추가 카드 스트리밍")
public class CardController {

    private final CardRequestService cardRequestService;
    private final LectureService lectureService;

    // QnA 스트리밍
    @Operation(summary = "QnA 확장 카드 스트리밍 시작")
    @PostMapping("/start-qna-stream")
    public ApiResponse<Void> startQnaStream(
            @AuthenticationPrincipal Long userId,
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam String qnaType
    ) {
        // 다른 사용자의 강의로 AI 생성을 요청하지 못하도록 소유자를 확인. 아니면 404
        lectureService.getOwned(lectureId, userId);
        cardRequestService.requestExtraQna(lectureId, sectionIndex, qnaType);
        return ApiResponse.ok();
    }

    // Resource 스트리밍
    @Operation(summary = "Resource 확장 카드 스트리밍 시작")
    @PostMapping("/start-resources-stream")
    public ApiResponse<Void> startResourceStream(
            @AuthenticationPrincipal Long userId,
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex,
            @RequestParam String resourceType
    ) {
        // 다른 사용자의 강의로 AI 생성을 요청하지 못하도록 소유자를 확인. 아니면 404
        lectureService.getOwned(lectureId, userId);
        cardRequestService.requestExtraResource(lectureId, sectionIndex, resourceType);
        return ApiResponse.ok();
    }
}
