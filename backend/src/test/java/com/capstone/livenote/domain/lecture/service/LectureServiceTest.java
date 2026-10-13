package com.capstone.livenote.domain.lecture.service;

import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
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

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class LectureServiceTest {

    @Mock LectureRepository lectureRepo;
    @Mock TranscriptRepository transcriptRepository;
    @Mock SummaryRepository summaryRepository;
    @Mock ResourceRepository resourceRepository;
    @Mock QnaRepository qnaRepository;
    @Mock BookmarkRepository bookmarkRepository;

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
}
