package com.livenote.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "transcripts")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Transcript {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;
    
    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;
    
    @Column(name = "start_sec")
    private Double startSec;
    
    @Column(name = "end_sec")
    private Double endSec;
    
    @Column(columnDefinition = "TEXT")
    private String text;
}

