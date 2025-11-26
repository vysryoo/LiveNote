package com.livenote.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "lectures")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Lecture {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "user_id", nullable = false)
    private Long userId;
    
    @Column(nullable = false)
    private String title;
    
    private String subject;
    
    @Column(name = "stt_language")
    private String sttLanguage;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private LectureStatus status;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "end_at")
    private LocalDateTime endAt;
    
    @Column(name = "duration")
    private Long duration; // seconds
    
    public enum LectureStatus {
        recording, completed
    }
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (status == null) {
            status = LectureStatus.recording;
        }
    }
}

