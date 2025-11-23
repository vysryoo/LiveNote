package com.capstone.livenote.domain.lecture.dto;

import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class SessionDetailResponse {
    private Long id;
    private Long userId;
    private String title;
    private String subject;
    private String sttLanguage;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime endAt;
    private Integer duration; // 강의 진행 시간 (초 단위)
    
    private List<TranscriptResponseDto> transcripts;
    private List<SummaryResponseDto> summaries;
    private List<ResourceResponseDto> resources;
    private List<QnaResponseDto> qna;
    private List<BookmarkResponseDto> bookmarks;

    public static SessionDetailResponse from(
            Lecture lecture,
            List<TranscriptResponseDto> transcripts,
            List<SummaryResponseDto> summaries,
            List<ResourceResponseDto> resources,
            List<QnaResponseDto> qna,
            List<BookmarkResponseDto> bookmarks
    ) {
        SessionDetailResponse response = new SessionDetailResponse();
        response.setId(lecture.getId());
        response.setUserId(lecture.getUserId());
        response.setTitle(lecture.getTitle());
        response.setSubject(lecture.getSubject());
        response.setSttLanguage(lecture.getSttLanguage());
        response.setStatus(lecture.getStatus().name());
        response.setCreatedAt(lecture.getCreatedAt());
        response.setEndAt(lecture.getEndAt());
        
        // duration 계산 (녹화 중이거나 종료된 경우)
        if (lecture.getEndAt() != null && lecture.getCreatedAt() != null) {
            response.setDuration((int) java.time.Duration.between(lecture.getCreatedAt(), lecture.getEndAt()).getSeconds());
        }
        
        response.setTranscripts(transcripts);
        response.setSummaries(summaries);
        response.setResources(resources);
        response.setQna(qna);
        response.setBookmarks(bookmarks);
        
        return response;
    }
}
