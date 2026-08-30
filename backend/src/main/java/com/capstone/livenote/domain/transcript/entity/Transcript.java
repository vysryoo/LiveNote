package com.capstone.livenote.domain.transcript.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
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
    private Integer sectionIndex;    // = startSec / 30

    @Column(name = "start_sec", nullable = false)
    private Integer startSec;

    @Column(name = "end_sec", nullable = false)
    private Integer endSec;

    @Lob
    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String text;

}
