package com.livenote.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "qna")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class QnA {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;
    
    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private QnAType type;
    
    @Column(columnDefinition = "TEXT")
    private String question;
    
    @Column(columnDefinition = "TEXT")
    private String answer;
    
    public enum QnAType {
        concept, application, advanced, comparison
    }
}

