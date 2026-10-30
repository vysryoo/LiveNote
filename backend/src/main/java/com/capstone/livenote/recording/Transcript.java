package com.capstone.livenote.recording;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "transcripts")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Transcript {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;    // 녹음 중 SectionAggregationService가 정함

    @Column(name = "start_sec", nullable = false)
    private Integer startSec;

    @Column(name = "end_sec", nullable = false)
    private Integer endSec;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String text;

}
