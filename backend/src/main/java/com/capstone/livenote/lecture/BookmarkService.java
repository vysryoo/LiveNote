package com.capstone.livenote.lecture;

import com.capstone.livenote.card.QnaRepository;
import com.capstone.livenote.card.ResourceRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

/**
 * 북마크의 생성과 삭제를 맡는다. 북마크 목록은 강의 상세 조회에 함께 담긴다.
 */
@Service
@RequiredArgsConstructor
public class BookmarkService {

    private final BookmarkRepository bookmarkRepository;
    private final QnaRepository qnaRepository;
    private final ResourceRepository resourceRepository;
    private final LectureService lectureService;

    /**
     * 사용자 본인 강의의 QnA나 자료 카드에 북마크를 단다.
     *
     * @param req 북마크 정보
     * @param userId 요청한 사용자 ID
     * @return 저장한 북마크
     * @throws IllegalArgumentException 대상 종류가 없거나 이미 북마크한 카드인 경우
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우, 또는 카드가 그 강의에 없는 경우
     */
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

    /**
     * 사용자 본인의 북마크를 삭제한다.
     *
     * @param userId 요청한 사용자 ID
     * @param bookmarkId 북마크 ID
     * @throws EntityNotFoundException 북마크가 없거나 다른 사용자의 북마크인 경우
     */
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
