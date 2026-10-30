package com.capstone.livenote.domain.bookmark.service;

import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class BookmarkService {

    private final BookmarkRepository bookmarkRepository;
    private final QnaRepository qnaRepository;
    private final ResourceRepository resourceRepository;
    private final LectureService lectureService;

    // 북마크 생성
    @Transactional
    public Bookmark createBookmark(CreateBookmarkRequestDto req, Long userId) {
        // 1. Enum 변환
        Bookmark.TargetType type = req.getTargetType();

        if (type == null) {
            throw new IllegalArgumentException("Invalid target type (must be RESOURCE or QNA)");
        }

        // 다른 사용자의 강의나 다른 강의의 카드를 가리키는 북마크가 저장되지 않도록 확인
        lectureService.getOwned(req.getLectureId(), userId);
        if (!isTargetInLecture(type, req.getTargetId(), req.getLectureId())) {
            throw new EntityNotFoundException("bookmark target");
        }

        // 2. 중복 체크
        if (bookmarkRepository.existsByUserIdAndTargetTypeAndTargetId(userId, type, req.getTargetId())) {
            throw new IllegalArgumentException("이미 북마크된 아이템입니다.");
        }

        // 3. 저장
        Bookmark bookmark = Bookmark.builder()
                .userId(userId)
                .lectureId(req.getLectureId())
                .sectionIndex(req.getSectionIndex())
                .targetType(type)
                .targetId(req.getTargetId())
                .build();

        return bookmarkRepository.save(bookmark);
    }

    // 북마크 삭제
    @Transactional
    public void deleteBookmark(Long userId, Long bookmarkId) {
        // 다른 사용자의 북마크도 없는 북마크와 같은 응답으로 처리해 존재 여부를 드러내지 않음
        Bookmark b = bookmarkRepository.findByIdAndUserId(bookmarkId, userId)
                .orElseThrow(() -> new EntityNotFoundException("bookmark"));

        bookmarkRepository.delete(b);
    }

    private boolean isTargetInLecture(Bookmark.TargetType type, Long targetId, Long lectureId) {
        return switch (type) {
            case QNA -> qnaRepository.existsByIdAndLectureId(targetId, lectureId);
            case RESOURCE -> resourceRepository.existsByIdAndLectureId(targetId, lectureId);
        };
    }
}
