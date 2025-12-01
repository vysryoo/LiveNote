package com.capstone.livenote.domain.bookmark.service;

import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class BookmarkService {

    @Autowired
    private BookmarkRepository bookmarkRepository;

    // 북마크 생성
    @Transactional
    public Bookmark createBookmark(CreateBookmarkRequestDto req, Long userId) {
        Bookmark.TargetType targetType = Bookmark.TargetType.fromString(req.getTargetType());
        if (targetType == null) {
            throw new org.springframework.web.server.ResponseStatusException(
                    org.springframework.http.HttpStatus.BAD_REQUEST, "invalid targetType");
        }

        var existing = bookmarkRepository.findByUserIdAndLectureIdAndSectionIndexAndTargetTypeAndTargetId(
                userId, req.getLectureId(), req.getSectionIndex(), targetType, req.getTargetId()
        );
        if (existing.isPresent()) {
            return existing.get();
        }

        Bookmark bookmark = Bookmark.builder()
                .userId(userId)
                .lectureId(req.getLectureId())
                .sectionIndex(req.getSectionIndex())
                .targetType(targetType)
                .targetId(req.getTargetId())
                .build();

        return bookmarkRepository.save(bookmark);
    }

    // 북마크 조회
    @Transactional(readOnly = true)
    public List<Bookmark> getBookmarks(Long userId, Long lectureId, Integer sectionIndex, Pageable pageable) {
        if (sectionIndex == null) {
            return bookmarkRepository.findByUserIdAndLectureId(userId, lectureId, pageable).getContent();
        }
        return bookmarkRepository
                .findByUserIdAndLectureIdAndSectionIndex(userId, lectureId, sectionIndex, pageable)
                .getContent();
    }

    // 북마크 삭제
    @Transactional
    public void deleteBookmark(Long userId, Long bookmarkId) {
        Bookmark b = bookmarkRepository.findById(bookmarkId)
                .orElseThrow(() -> new RuntimeException("Bookmark not found"));

        if (!b.getUserId().equals(userId)) {
            throw new RuntimeException("No permission to delete this bookmark");
        }

        bookmarkRepository.delete(b);
    }
}
