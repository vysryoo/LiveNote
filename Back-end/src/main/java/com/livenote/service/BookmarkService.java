package com.livenote.service;

import com.livenote.dto.BookmarkDto;
import com.livenote.dto.BookmarkRequest;
import com.livenote.entity.Bookmark;
import com.livenote.entity.Lecture;
import com.livenote.repository.BookmarkRepository;
import com.livenote.repository.LectureRepository;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class BookmarkService {
    private final BookmarkRepository bookmarkRepository;
    private final LectureRepository lectureRepository;

    @Transactional
    public BookmarkDto addBookmark(BookmarkRequest request) {
        Long userId = SecurityUtil.getCurrentUserId();

        Lecture lecture = lectureRepository.findById(request.getLectureId())
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        Bookmark bookmark = Bookmark.builder()
                .userId(userId)
                .lectureId(request.getLectureId())
                .sectionIndex(request.getSectionIndex())
                .targetType(Bookmark.BookmarkTargetType.valueOf(request.getTargetType()))
                .targetId(request.getTargetId())
                .build();

        bookmark = bookmarkRepository.save(bookmark);
        return toDto(bookmark);
    }

    @Transactional(readOnly = true)
    public List<BookmarkDto> getBookmarks(Long lectureId, Integer sectionIndex) {
        Long userId = SecurityUtil.getCurrentUserId();
        return bookmarkRepository.findByUserIdAndLectureIdAndSectionIndex(userId, lectureId, sectionIndex)
                .stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    @Transactional
    public void deleteBookmark(Long bookmarkId) {
        Long userId = SecurityUtil.getCurrentUserId();
        Bookmark bookmark = bookmarkRepository.findById(bookmarkId)
                .orElseThrow(() -> new RuntimeException("북마크를 찾을 수 없습니다"));

        if (!bookmark.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        bookmarkRepository.delete(bookmark);
    }

    private BookmarkDto toDto(Bookmark bookmark) {
        return BookmarkDto.builder()
                .id(bookmark.getId())
                .userId(bookmark.getUserId())
                .lectureId(bookmark.getLectureId())
                .sectionIndex(bookmark.getSectionIndex())
                .targetType(bookmark.getTargetType().name())
                .targetId(bookmark.getTargetId())
                .build();
    }
}

