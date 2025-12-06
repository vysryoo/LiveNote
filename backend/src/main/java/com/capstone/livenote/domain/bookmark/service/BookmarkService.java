package com.capstone.livenote.domain.bookmark.service;

import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
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
    private final BookmarkRepository bookmarkRepository;
    private final QnaRepository qnaRepository;
    private final ResourceRepository resourceRepository;

    // 북마크 생성
    @Transactional
    public Bookmark createBookmark(CreateBookmarkRequestDto req, Long userId) {
        // 1. Enum 변환
        Bookmark.TargetType type = req.getTargetType();

        if (type == null) {
            throw new IllegalArgumentException("Invalid target type (must be RESOURCE or QNA)");
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

    // 북마크 조회
    @Transactional(readOnly = true)
    public List<BookmarkResponseDto> getBookmarks(Long userId, Long lectureId, Integer sectionIndex, Pageable pageable) {



        System.out.println("[BookmarkService] getBookmarks userId=" + userId
                + ", lectureId=" + lectureId
                + ", sectionIndex=" + sectionIndex);

        List<Bookmark> bookmarks;

        if (sectionIndex != null) {
            // 섹션 필터링
            bookmarks = bookmarkRepository.findByUserIdAndLectureIdAndSectionIndex(userId, lectureId, sectionIndex);
        } else {

            bookmarks = bookmarkRepository.findByUserIdAndLectureId(userId, lectureId);
        }

        System.out.println("[BookmarkService] bookmarks size=" + bookmarks.size());

        return bookmarks.stream().map(bm -> {
            Object content = null;

            try {
                if (bm.getTargetType() == Bookmark.TargetType.QNA) {
                    content = qnaRepository.findById(bm.getTargetId())
                            .map(QnaResponseDto::from)
                            .orElse(null);
                } else if (bm.getTargetType() == Bookmark.TargetType.RESOURCE) {
                    content = resourceRepository.findById(bm.getTargetId())
                            .map(ResourceResponseDto::from)
                            .orElse(null);
                }
            } catch (Exception e) {
                // 조회 중 에러가 나도 전체 리스트를 망치지 않도록 로그만 찍고 넘어감
                System.err.println("Error fetching content for bookmark " + bm.getId() + ": " + e.getMessage());
            }

            System.out.println("[BookmarkService] bm id=" + bm.getId()
                    + ", targetType=" + bm.getTargetType()
                    + ", targetId=" + bm.getTargetId());

            return BookmarkResponseDto.from(bm, content);
        }).toList();
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
