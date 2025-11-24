package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SessionDetailResponse {
    private Long id;
    private Long userId;
    private String title;
    private String subject;
    private String sttLanguage;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime endAt;
    private Long duration;
    private List<TranscriptDto> transcripts;
    private List<SummaryDto> summaries;
    private List<ResourceDto> resources;
    private List<QnADto> qna;
    private List<BookmarkDto> bookmarks;
}

