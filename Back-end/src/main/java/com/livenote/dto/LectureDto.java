package com.livenote.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LectureDto {
    private Long id;
    private Long userId;
    private String title;
    private String subject;
    private String sttLanguage;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime endAt;
    private Long duration;
}

