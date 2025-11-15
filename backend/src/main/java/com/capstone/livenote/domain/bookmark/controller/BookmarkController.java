package com.capstone.livenote.domain.bookmark.controller;

import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.service.BookmarkService;
import com.capstone.livenote.global.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bookmarks")
public class BookmarkController {

    @Autowired
    private BookmarkService bookmarkService;

    private Long currentUserId() {
        // JWT 완성 시 토큰에서 가져올예정
        return 1L;
    }

    // === 북마크 생성 ===
    @PostMapping
    public ApiResponse<BookmarkResponseDto> createBookmark(@RequestBody CreateBookmarkRequestDto dto) {
        Bookmark b = bookmarkService.createBookmark(dto, currentUserId());
        return ApiResponse.ok(BookmarkResponseDto.from(b));
    }

    // === 북마크 목록 조회 ===
    @GetMapping
    public ApiResponse<List<BookmarkResponseDto>> getBookmarks(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex
    ) {
        var bookmarks = bookmarkService.getBookmarks(currentUserId(), lectureId, sectionIndex);
        var responseList = bookmarks.stream()
                .map(b -> new BookmarkResponseDto(
                        b.getId(),
                        b.getLectureId(),
                        b.getSectionIndex(),
                        b.getTargetType().name().toLowerCase(),
                        b.getTargetId()
                ))
                .toList();

        return ApiResponse.ok(responseList);
    }

    // === 북마크 삭제 ===
    @DeleteMapping("/{bookmarkId}")
    public ApiResponse<Void> deleteBookmark(@PathVariable Long bookmarkId) {
        bookmarkService.deleteBookmark(currentUserId(), bookmarkId);
        return ApiResponse.ok(null);
    }

//    private BookmarkResponseDto toDto(Bookmark b) {
//        return new BookmarkResponseDto(
//                b.getId(), b.getUserId(), b.getLectureId(),
//                b.getSectionIndex(), b.getTargetType().name().toLowerCase(), b.getTargetId()
//        );
//    }
}