package com.capstone.livenote.domain.lecture.dto;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.sql.Timestamp;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class LectureResponseDto {
    private Long id;
    private Long userId;
    private String title;
    private String subject;
    private String sttLanguage;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime endAt;

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
