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
    private String title;
    private String subject;
    private String sttLanguage;
    private String status;
    private LocalDateTime createdAt;
    private LocalDateTime endAt;

//    public LectureResponseDto(Long id, String title, String subject, String language, Lecture.Status status, LocalDateTime createdAt, LocalDateTime endAt) {
//        this.id = id;
//        this.title = title;
//        this.subject = subject;
//        this.sttLanguage = language;
//        this.status = status.name();
//        this.createdAt = createdAt;
//        this.endAt = endAt;
//    }


    public static LectureResponseDto from(Lecture l) {
        return new LectureResponseDto(
                l.getId(),
                l.getTitle(),
                l.getSubject(),
                l.getSttLanguage(),
                l.getStatus().name(),
                l.getCreatedAt(),
                l.getEndAt()
        );
    }

}