package com.capstone.livenote.summary;

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

    /** 섹션 번호. 녹음 중 SectionAggregationService가 정한 전사의 섹션 번호와 같음 */
    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;

    @Column(nullable = false)
    private Integer startSec;

    @Column(nullable = false)
    private Integer endSec;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String text;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    @Builder.Default
    private SummaryPhase phase = SummaryPhase.FINAL;

    @PrePersist
    public void ensurePhase() {
        if (phase == null) {
            phase = SummaryPhase.FINAL;
        }
    }

}
