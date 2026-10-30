package com.capstone.livenote.domain.bookmark.service;

import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class BookmarkServiceTest {

    @Mock BookmarkRepository bookmarkRepository;
    @Mock QnaRepository qnaRepository;
    @Mock ResourceRepository resourceRepository;

    @InjectMocks
    BookmarkService service;

    @Test
    void deleteBookmark_deletesOwnBookmark() {
        Bookmark bookmark = Bookmark.builder().id(3L).userId(1L).build();
        when(bookmarkRepository.findByIdAndUserId(3L, 1L)).thenReturn(Optional.of(bookmark));

        service.deleteBookmark(1L, 3L);

        verify(bookmarkRepository).delete(bookmark);
    }

    @Test
    void deleteBookmark_throwsNotFoundForMissingOrOtherUsersBookmark() {
        // 다른 사용자의 북마크는 저장소 조건(id, userId)에 걸리지 않아 없는 북마크와 같은 결과가 됨
        when(bookmarkRepository.findByIdAndUserId(3L, 2L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.deleteBookmark(2L, 3L))
                .isInstanceOf(EntityNotFoundException.class);
        verify(bookmarkRepository, never()).delete(any());
    }
}
