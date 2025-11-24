package com.livenote.controller;

import com.livenote.dto.BookmarkDto;
import com.livenote.dto.BookmarkRequest;
import com.livenote.service.BookmarkService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/bookmarks")
@RequiredArgsConstructor
public class BookmarkController {
    private final BookmarkService bookmarkService;

    @PostMapping
    public ResponseEntity<BookmarkDto> addBookmark(@Valid @RequestBody BookmarkRequest request) {
        return ResponseEntity.ok(bookmarkService.addBookmark(request));
    }

    @GetMapping
    public ResponseEntity<List<BookmarkDto>> getBookmarks(
            @RequestParam Long lectureId,
            @RequestParam Integer sectionIndex) {
        return ResponseEntity.ok(bookmarkService.getBookmarks(lectureId, sectionIndex));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteBookmark(@PathVariable Long id) {
        bookmarkService.deleteBookmark(id);
        return ResponseEntity.noContent().build();
    }
}

