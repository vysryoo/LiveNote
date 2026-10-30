package com.capstone.livenote.domain.lecture.service;

import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.dto.SessionDetailResponse;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.SliceImpl;
import org.springframework.mock.web.MockMultipartFile;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class LectureServiceTest {

    @Mock LectureRepository lectureRepo;
    @Mock TranscriptRepository transcriptRepository;
    @Mock SummaryRepository summaryRepository;
    @Mock ResourceRepository resourceRepository;
    @Mock QnaRepository qnaRepository;
    @Mock BookmarkRepository bookmarkRepository;
    @Mock RagClient ragClient;

    @InjectMocks
    LectureService service;

    @Test
    void getOwned_returnsLectureOfRequester() {
        Lecture lecture = Lecture.builder().id(7L).userId(1L).title("자료구조").build();
        when(lectureRepo.findByIdAndUserId(7L, 1L)).thenReturn(Optional.of(lecture));

        assertThat(service.getOwned(7L, 1L)).isSameAs(lecture);
    }

    @Test
    void getOwned_throwsNotFoundForOtherUsersLecture() {
        // 다른 사용자의 강의는 저장소 조건(id, userId)에 걸리지 않아 없는 강의와 같은 결과가 됨
        when(lectureRepo.findByIdAndUserId(7L, 2L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.getOwned(7L, 2L))
                .isInstanceOf(EntityNotFoundException.class);
    }

    @Test
    void endLecture_savesTitleAndCompletes() {
        Lecture lecture = Lecture.builder().id(4L).userId(1L).title("old").status(Lecture.Status.RECORDING).build();
        when(lectureRepo.findByIdAndUserId(4L, 1L)).thenReturn(Optional.of(lecture));

        Lecture ended = service.endLecture(4L, 1L, "  자료구조 3주차 ");

        assertThat(ended.getTitle()).isEqualTo("자료구조 3주차");
        assertThat(ended.getStatus()).isEqualTo(Lecture.Status.COMPLETED);
        assertThat(ended.getEndAt()).isNotNull();
    }

    @Test
    void endLecture_withoutTitleKeepsExistingTitle() {
        Lecture lecture = Lecture.builder().id(4L).userId(1L).title("old").status(Lecture.Status.RECORDING).build();
        when(lectureRepo.findByIdAndUserId(4L, 1L)).thenReturn(Optional.of(lecture));

        assertThat(service.endLecture(4L, 1L, null).getTitle()).isEqualTo("old");
        assertThat(service.endLecture(4L, 1L, "   ").getTitle()).isEqualTo("old");
    }

    @Test
    void endLecture_throwsNotFoundForOtherUsersLecture() {
        when(lectureRepo.findByIdAndUserId(4L, 2L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.endLecture(4L, 2L, "제목"))
                .isInstanceOf(EntityNotFoundException.class);
        verify(lectureRepo, never()).save(any());
    }

    @Test
    void getSessionDetail_returnsBookmarksWithoutLoadingTargets() {
        Lecture lecture = Lecture.builder().id(4L).userId(1L).title("강의").status(Lecture.Status.RECORDING).build();
        Bookmark bookmark = Bookmark.builder().id(3L).userId(1L).lectureId(4L).sectionIndex(0)
                .targetType(Bookmark.TargetType.QNA).targetId(9L).build();
        when(lectureRepo.findByIdAndUserId(4L, 1L)).thenReturn(Optional.of(lecture));
        when(resourceRepository.findByLectureId(eq(4L), any())).thenReturn(Page.empty());
        when(bookmarkRepository.findByUserIdAndLectureId(eq(1L), eq(4L), any())).thenReturn(new SliceImpl<>(List.of(bookmark)));

        SessionDetailResponse detail = service.getSessionDetail(4L, 1L);

        assertThat(detail.getBookmarks()).extracting(BookmarkResponseDto::getTargetId).containsExactly(9L);
        verify(qnaRepository, never()).findById(any());
        verify(resourceRepository, never()).findById(any());
    }

    @Test
    void createWithPdf_savesCollectionIdOfUploadedPdf() {
        var pdf = new MockMultipartFile("files", "slides.pdf", "application/pdf", new byte[]{1});
        when(lectureRepo.save(any())).thenAnswer(invocation -> {
            Lecture lecture = invocation.getArgument(0);
            if (lecture.getId() == null) lecture.setId(9L);
            return lecture;
        });
        when(ragClient.upsertPdf(9L, pdf, null)).thenReturn("lecture_9");

        Lecture created = service.createWithPdf(1L, new CreateLectureRequestDto("제목", "과목", "ko"), pdf);

        assertThat(created.getCollectionId()).isEqualTo("lecture_9");
        assertThat(created.getUserId()).isEqualTo(1L);
    }

    @Test
    void createWithPdf_keepsLectureWhenUploadFails() {
        var pdf = new MockMultipartFile("files", "slides.pdf", "application/pdf", new byte[]{1});
        when(lectureRepo.save(any())).thenAnswer(invocation -> {
            Lecture lecture = invocation.getArgument(0);
            lecture.setId(9L);
            return lecture;
        });
        when(ragClient.upsertPdf(9L, pdf, null)).thenThrow(new RuntimeException("RAG Upsert Failed"));

        assertThatThrownBy(() -> service.createWithPdf(1L, new CreateLectureRequestDto("제목", "과목", "ko"), pdf))
                .isInstanceOf(RuntimeException.class);
        // 강의는 업로드 전에 저장되어 남고, 컬렉션 ID 저장은 일어나지 않음
        verify(lectureRepo, times(1)).save(any());
    }
}
