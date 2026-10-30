package com.capstone.livenote.lecture;

import com.capstone.livenote.card.QnaRepository;
import com.capstone.livenote.card.ResourceRepository;
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
        Bookmark.TargetType type = req.targetType();

        if (type == null) {
            throw new IllegalArgumentException("Invalid target type (must be RESOURCE or QNA)");
        }

        // 다른 사용자의 강의나 다른 강의의 카드를 가리키는 북마크가 저장되지 않도록 확인
        lectureService.getOwned(req.lectureId(), userId);
        if (!isTargetInLecture(type, req.targetId(), req.lectureId())) {
            throw new EntityNotFoundException("bookmark target");
        }

        if (bookmarkRepository.existsByUserIdAndTargetTypeAndTargetId(userId, type, req.targetId())) {
            throw new IllegalArgumentException("이미 북마크된 아이템입니다.");
        }

        Bookmark bookmark = Bookmark.builder()
                .userId(userId)
                .lectureId(req.lectureId())
                .sectionIndex(req.sectionIndex())
                .targetType(type)
                .targetId(req.targetId())
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
