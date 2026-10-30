package com.capstone.livenote.lecture;

import com.capstone.livenote.card.QnaResponseDto;
import com.capstone.livenote.card.ResourceResponseDto;
import com.capstone.livenote.summary.SummaryResponseDto;
import com.capstone.livenote.recording.TranscriptResponseDto;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;

public record SessionDetailResponse(
        Long id,
        Long userId,
        String title,
        String subject,
        String sttLanguage,
        String status,
        LocalDateTime createdAt,
        LocalDateTime endAt,
        Integer duration, // 강의 진행 시간 (초 단위). 종료 전이면 null
        List<TranscriptResponseDto> transcripts,
        List<SummaryResponseDto> summaries,
        List<ResourceResponseDto> resources,
        List<QnaResponseDto> qna,
        List<BookmarkResponseDto> bookmarks
) {

    public static SessionDetailResponse from(
            Lecture lecture,
            List<TranscriptResponseDto> transcripts,
            List<SummaryResponseDto> summaries,
            List<ResourceResponseDto> resources,
            List<QnaResponseDto> qna,
            List<BookmarkResponseDto> bookmarks
    ) {
        Integer duration = null;
        if (lecture.getEndAt() != null && lecture.getCreatedAt() != null) {
            duration = (int) Duration.between(lecture.getCreatedAt(), lecture.getEndAt()).getSeconds();
        }
        return new SessionDetailResponse(
                lecture.getId(),
                lecture.getUserId(),
                lecture.getTitle(),
                lecture.getSubject(),
                lecture.getSttLanguage(),
                lecture.getStatus().name(),
                lecture.getCreatedAt(),
                lecture.getEndAt(),
                duration,
                transcripts,
                summaries,
                resources,
                qna,
                bookmarks
        );
    }
}
