package com.capstone.livenote.lecture;

import java.time.LocalDateTime;

public record LectureResponseDto(
        Long id,
        Long userId,
        String title,
        String subject,
        String sttLanguage,
        String status,
        LocalDateTime createdAt,
        LocalDateTime endAt
) {

    public static LectureResponseDto from(Lecture l) {
        return new LectureResponseDto(
                l.getId(),
                l.getUserId(),
                l.getTitle(),
                l.getSubject(),
                l.getSttLanguage(),
                l.getStatus().name(),
                l.getCreatedAt(),
                l.getEndAt()
        );
    }
}
