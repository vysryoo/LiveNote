package com.capstone.livenote.lecture;

import com.capstone.livenote.card.QnaRepository;
import com.capstone.livenote.card.ResourceRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class BookmarkServiceTest {

    @Mock BookmarkRepository bookmarkRepository;
    @Mock QnaRepository qnaRepository;
    @Mock ResourceRepository resourceRepository;

    @Mock LectureService lectureService;

    @InjectMocks
    BookmarkService service;

    @Test
    void createBookmark_savesTargetOfOwnLecture() {
        when(resourceRepository.existsByIdAndLectureId(9L, 5L)).thenReturn(true);
        when(bookmarkRepository.save(any())).thenAnswer(invocation -> invocation.getArgument(0));

        Bookmark saved = service.createBookmark(
                new CreateBookmarkRequestDto(5L, 0, Bookmark.TargetType.RESOURCE, 9L), 1L);

        verify(lectureService).getOwned(5L, 1L);
        assertThat(saved.getUserId()).isEqualTo(1L);
        assertThat(saved.getTargetId()).isEqualTo(9L);
    }

    @Test
    void createBookmark_rejectsOtherUsersLecture() {
        when(lectureService.getOwned(5L, 2L)).thenThrow(new EntityNotFoundException("lecture"));

        assertThatThrownBy(() -> service.createBookmark(
                new CreateBookmarkRequestDto(5L, 0, Bookmark.TargetType.QNA, 9L), 2L))
                .isInstanceOf(EntityNotFoundException.class);
        verify(bookmarkRepository, never()).save(any());
    }

    @Test
    void createBookmark_rejectsTargetOfAnotherLecture() {
        when(qnaRepository.existsByIdAndLectureId(9L, 5L)).thenReturn(false);

        assertThatThrownBy(() -> service.createBookmark(
                new CreateBookmarkRequestDto(5L, 0, Bookmark.TargetType.QNA, 9L), 1L))
                .isInstanceOf(EntityNotFoundException.class);
        verify(bookmarkRepository, never()).save(any());
    }

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
