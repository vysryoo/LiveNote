package com.capstone.livenote.domain.bookmark.controller;

import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.service.BookmarkService;
import com.capstone.livenote.global.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;


@Tag(name = "Bookmark API", description = "북마크 API")
@RestController
@RequestMapping("/api/bookmarks")
@RequiredArgsConstructor
public class BookmarkController {

    private final BookmarkService bookmarkService;

    private Long currentUserId() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !authentication.isAuthenticated()) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.UNAUTHORIZED, "not authenticated");
        }
        String userIdStr = authentication.getName();
        try {
            return Long.parseLong(userIdStr);
        } catch (NumberFormatException e) {
            throw new ResponseStatusException(org.springframework.http.HttpStatus.UNAUTHORIZED, "invalid user id");
        }
    }

    // 북마크 생성
    @Operation(summary = "현재 강의 구간에 북마크를 추가")
    @PostMapping
    public ApiResponse<BookmarkResponseDto> createBookmark(
            @RequestBody CreateBookmarkRequestDto req
    ) {
        Bookmark bookmark = bookmarkService.createBookmark(req, currentUserId());
        return ApiResponse.ok(BookmarkResponseDto.from(bookmark));
    }

    // 북마크 목록 조회
    @Operation(summary = "특정 강의의 북마크 목록을 조회")
    @GetMapping
    public ApiResponse<List<BookmarkResponseDto>> getBookmarks(
            @RequestParam Long lectureId,
            @RequestParam(required = false) Integer sectionIndex,
            @PageableDefault(size = 50) Pageable pageable
    ) {
        var list = bookmarkService.getBookmarks(
                        currentUserId(), lectureId, sectionIndex, pageable
                ).stream()
                .map(BookmarkResponseDto::from)
                .toList();

        return ApiResponse.ok(list);
    }

    // 북마크 삭제
    @Operation(summary = "지정한 북마크를 삭제")
    @DeleteMapping("/{bookmarkId}")
    public ApiResponse<Void> deleteBookmark(@PathVariable Long bookmarkId) {
        bookmarkService.deleteBookmark(currentUserId(), bookmarkId);
        return ApiResponse.ok(null);
    }

}
