package com.capstone.livenote.domain.summary.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import jakarta.persistence.*;
import lombok.*;


@Entity
@Table(name = "summaries",
        uniqueConstraints = @UniqueConstraint(columnNames = {"lecture_id","chunkIndex"}),
        indexes = {
                @Index(name="idx_summaries_lecture_chunk", columnList = "lecture_id, chunkIndex"),
                @Index(name="idx_summaries_lecture_start", columnList = "lecture_id, startSec")
        })
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Summary {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex; // StartSec / 30

    @Column(nullable = false)
    private Integer startSec;

    @Column(nullable = false)
    private Integer endSec;

    @Lob @Column(nullable = false)
    private String text; // 요약텍스트
}