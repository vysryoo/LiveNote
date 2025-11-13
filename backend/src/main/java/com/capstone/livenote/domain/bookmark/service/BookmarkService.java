package com.capstone.livenote.domain.bookmark.service;

import com.capstone.livenote.domain.bookmark.dto.CreateBookmarkRequestDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Slice;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class BookmarkService {

    @Autowired
    private BookmarkRepository bookmarkRepo;

    // === 북마크 생성 ===
    @Transactional
    public Bookmark createBookmark(CreateBookmarkRequestDto dto, Long userId) {
        // 중복 확인
//        Optional<Bookmark> exist = bookmarkRepo.findByUserIdAndLectureIdAndSectionIndexAndTargetTypeAndTargetId(
//                userId, dto.getLectureId(), dto.getSectionIndex(),
//                Bookmark.TargetType.valueOf(dto.getTargetType().toUpperCase()), dto.getTargetId()
//        );

        //if (exist.isPresent()) return exist.get();

        Bookmark bookmark = Bookmark.builder()
                .userId(userId)
                .lectureId(dto.getLectureId())
                .sectionIndex(dto.getSectionIndex())
                .targetType(Bookmark.TargetType.valueOf(dto.getTargetType().toUpperCase()))
                .targetId(dto.getTargetId())
                .build();

        return bookmarkRepo.save(bookmark);
    }

    // === 강의+섹션별 북마크 조회 ===
    @Transactional(readOnly = true)
    public List<Bookmark> getBookmarks(Long userId, Long lectureId, Integer sectionIndex) {
        return bookmarkRepo
                .findByUserIdAndLectureIdAndSectionIndex(userId, lectureId, sectionIndex, null)
                .getContent();
    }

    // === 북마크 삭제 ===
    @Transactional
    public void deleteBookmark(Long userId, Long bookmarkId) {
        Bookmark b = bookmarkRepo.findById(bookmarkId)
                .orElseThrow(() -> new RuntimeException("Bookmark not found"));

        if (!b.getUserId().equals(userId)) {
            throw new RuntimeException("No permission to delete this bookmark");
        }

        bookmarkRepo.delete(b);
    }
}