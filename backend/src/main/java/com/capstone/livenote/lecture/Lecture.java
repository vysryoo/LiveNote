package com.capstone.livenote.lecture;

import jakarta.persistence.*;
import lombok.*;
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
    @Builder.Default
    private Status status = Status.RECORDING;

    private LocalDateTime createdAt;
    private LocalDateTime endAt;

    private Integer duration; // 값을 채우지 않음. 응답의 진행 시간은 createdAt, endAt으로 계산함

    @Column(columnDefinition = "TEXT")
    private String files;

    @PrePersist void prePersist() {
        if (createdAt == null) createdAt = LocalDateTime.now();
    }

    // RAG 컬렉션 ID 저장용
    @Column(name = "collection_id")
    private String collectionId;
}
