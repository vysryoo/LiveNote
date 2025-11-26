package com.livenote.service;

import com.livenote.dto.*;
import com.livenote.entity.*;
import com.livenote.repository.*;
import com.livenote.util.SecurityUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class LectureService {
    private final LectureRepository lectureRepository;
    private final TranscriptRepository transcriptRepository;
    private final SummaryRepository summaryRepository;
    private final ResourceRepository resourceRepository;
    private final QnARepository qnARepository;
    private final BookmarkRepository bookmarkRepository;

    @Transactional(readOnly = true)
    public List<LectureDto> getLectures() {
        Long userId = SecurityUtil.getCurrentUserId();
        return lectureRepository.findByUserIdOrderByCreatedAtDesc(userId)
                .stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public SessionDetailResponse getLecture(Long id) {
        Long userId = SecurityUtil.getCurrentUserId();
        Lecture lecture = lectureRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        List<TranscriptDto> transcripts = transcriptRepository.findByLectureIdOrderBySectionIndexAsc(id)
                .stream()
                .map(this::toTranscriptDto)
                .collect(Collectors.toList());

        List<SummaryDto> summaries = summaryRepository.findByLectureIdOrderBySectionIndexAsc(id)
                .stream()
                .map(this::toSummaryDto)
                .collect(Collectors.toList());

        List<ResourceDto> resources = resourceRepository.findByLectureId(id)
                .stream()
                .map(this::toResourceDto)
                .collect(Collectors.toList());

        List<QnADto> qna = qnARepository.findByLectureId(id)
                .stream()
                .map(this::toQnADto)
                .collect(Collectors.toList());

        List<BookmarkDto> bookmarks = bookmarkRepository.findByUserIdAndLectureId(userId, id)
                .stream()
                .map(this::toBookmarkDto)
                .collect(Collectors.toList());

        return SessionDetailResponse.builder()
                .id(lecture.getId())
                .userId(lecture.getUserId())
                .title(lecture.getTitle())
                .subject(lecture.getSubject())
                .sttLanguage(lecture.getSttLanguage())
                .status(lecture.getStatus().name())
                .createdAt(lecture.getCreatedAt())
                .endAt(lecture.getEndAt())
                .duration(lecture.getDuration())
                .transcripts(transcripts)
                .summaries(summaries)
                .resources(resources)
                .qna(qna)
                .bookmarks(bookmarks)
                .build();
    }

    @Transactional
    public LectureDto createLecture(CreateLectureRequest request, List<MultipartFile> files) {
        Long userId = SecurityUtil.getCurrentUserId();

        Lecture lecture = Lecture.builder()
                .userId(userId)
                .title(request.getTitle())
                .subject(request.getSubject())
                .sttLanguage(request.getSttLanguage())
                .status(Lecture.LectureStatus.recording)
                .build();

        lecture = lectureRepository.save(lecture);

        // 파일 업로드 처리 (필요시 구현)
        if (files != null && !files.isEmpty()) {
            // 파일 저장 로직
        }

        return toDto(lecture);
    }

    @Transactional
    public LectureDto updateLectureTitle(Long id, UpdateLectureTitleRequest request) {
        Long userId = SecurityUtil.getCurrentUserId();
        Lecture lecture = lectureRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        lecture.setTitle(request.getTitle());
        lecture = lectureRepository.save(lecture);
        return toDto(lecture);
    }

    @Transactional
    public void deleteLecture(Long id) {
        Long userId = SecurityUtil.getCurrentUserId();
        Lecture lecture = lectureRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        lectureRepository.delete(lecture);
    }

    @Transactional
    public LectureDto endLecture(Long id, UpdateLectureTitleRequest request) {
        Long userId = SecurityUtil.getCurrentUserId();
        Lecture lecture = lectureRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("강의를 찾을 수 없습니다"));

        if (!lecture.getUserId().equals(userId)) {
            throw new RuntimeException("권한이 없습니다");
        }

        if (request != null && request.getTitle() != null) {
            lecture.setTitle(request.getTitle());
        }

        lecture.setStatus(Lecture.LectureStatus.completed);
        lecture.setEndAt(LocalDateTime.now());

        if (lecture.getCreatedAt() != null) {
            Duration duration = Duration.between(lecture.getCreatedAt(), lecture.getEndAt());
            lecture.setDuration(duration.getSeconds());
        }

        lecture = lectureRepository.save(lecture);
        return toDto(lecture);
    }

    private LectureDto toDto(Lecture lecture) {
        return LectureDto.builder()
                .id(lecture.getId())
                .userId(lecture.getUserId())
                .title(lecture.getTitle())
                .subject(lecture.getSubject())
                .sttLanguage(lecture.getSttLanguage())
                .status(lecture.getStatus().name())
                .createdAt(lecture.getCreatedAt())
                .endAt(lecture.getEndAt())
                .duration(lecture.getDuration())
                .build();
    }

    private TranscriptDto toTranscriptDto(Transcript transcript) {
        return TranscriptDto.builder()
                .id(transcript.getId())
                .lectureId(transcript.getLectureId())
                .sectionIndex(transcript.getSectionIndex())
                .startSec(transcript.getStartSec())
                .endSec(transcript.getEndSec())
                .text(transcript.getText())
                .build();
    }

    private SummaryDto toSummaryDto(Summary summary) {
        return SummaryDto.builder()
                .id(summary.getId())
                .lectureId(summary.getLectureId())
                .sectionIndex(summary.getSectionIndex())
                .startSec(summary.getStartSec())
                .endSec(summary.getEndSec())
                .text(summary.getText())
                .build();
    }

    public ResourceDto toResourceDto(Resource resource) {
        return ResourceDto.builder()
                .id(resource.getId())
                .lectureId(resource.getLectureId())
                .sectionIndex(resource.getSectionIndex())
                .type(resource.getType().name())
                .title(resource.getTitle())
                .text(resource.getText())
                .url(resource.getUrl())
                .thumbnail(resource.getThumbnail())
                .score(resource.getScore())
                .build();
    }

    public QnADto toQnADto(QnA qnA) {
        return QnADto.builder()
                .id(qnA.getId())
                .lectureId(qnA.getLectureId())
                .sectionIndex(qnA.getSectionIndex())
                .type(qnA.getType().name())
                .question(qnA.getQuestion())
                .answer(qnA.getAnswer())
                .build();
    }

    private BookmarkDto toBookmarkDto(Bookmark bookmark) {
        return BookmarkDto.builder()
                .id(bookmark.getId())
                .userId(bookmark.getUserId())
                .lectureId(bookmark.getLectureId())
                .sectionIndex(bookmark.getSectionIndex())
                .targetType(bookmark.getTargetType().name())
                .targetId(bookmark.getTargetId())
                .build();
    }
}

