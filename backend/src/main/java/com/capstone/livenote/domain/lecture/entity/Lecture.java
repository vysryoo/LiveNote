package com.capstone.livenote.domain.lecture.entity;

import com.capstone.livenote.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import java.sql.Timestamp;
import java.time.LocalDateTime;

@Entity
@Table(name = "lectures")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Lecture {

    public enum Status { RECORDING, COMPLETED }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false)
    private String title;

    private String subject;

    private String sttLanguage;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status = Status.RECORDING;

    private LocalDateTime createdAt;
    private LocalDateTime endAt;

    private Integer duration; // endAt - createdAt

    @Lob
    private String files;

    @PrePersist void prePersist() {
        if (createdAt == null) createdAt = java.time.LocalDateTime.now();
    }

    // RAG 컬렉션 ID 저장용
    @Column(name = "collection_id")
    private String collectionId;
}
