package com.capstone.livenote.domain.summary.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import jakarta.persistence.*;
import lombok.*;


@Entity
@Table(name = "summaries",
        uniqueConstraints = @UniqueConstraint(columnNames = {"lecture_id","section_index"}),
        indexes = {
                @Index(name="idx_summaries_lecture_section", columnList = "lecture_id, section_index"),
                @Index(name="idx_summaries_lecture_start", columnList = "lecture_id, startSec")
        })
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Summary {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    /**
     * 섹션 인덱스 (30초 단위)
     * 계산식: startSec / 30
     */
    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;

    @Column(nullable = false)
    private Integer startSec;

    @Column(nullable = false)
    private Integer endSec;

    @Lob
    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String text;

}
