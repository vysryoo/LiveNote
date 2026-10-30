package com.capstone.livenote.lecture;

import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;


@Tag(name = "Bookmark API", description = "북마크 API")
@RestController
@RequestMapping("/api/bookmarks")
@RequiredArgsConstructor
public class BookmarkController {

    private final BookmarkService bookmarkService;

    @Operation(summary = "현재 강의 구간에 북마크를 추가")
    @PostMapping
    public ApiResponse<BookmarkResponseDto> createBookmark(
            @AuthenticationPrincipal Long userId,
            @RequestBody CreateBookmarkRequestDto req
    ) {
        Bookmark bookmark = bookmarkService.createBookmark(req, userId);
        return ApiResponse.ok(BookmarkResponseDto.from(bookmark));
    }

    @Operation(summary = "지정한 북마크를 삭제")
    @DeleteMapping("/{bookmarkId}")
    public ApiResponse<Void> deleteBookmark(@AuthenticationPrincipal Long userId, @PathVariable Long bookmarkId) {
        bookmarkService.deleteBookmark(userId, bookmarkId);
        return ApiResponse.ok(null);
    }

}
