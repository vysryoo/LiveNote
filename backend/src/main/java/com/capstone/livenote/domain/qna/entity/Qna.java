package com.capstone.livenote.domain.qna.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "qna")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Qna {

    public enum Type{ CONCEPT, APPLICATION, ADVANCED, COMPARISON }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "summary_id")
    private Long summaryId;

    @Column(nullable = false)
    private Integer sectionIndex;

    @Enumerated(EnumType.STRING)
    private Type type;

    @Column(nullable = false)
    private String question;

    @Lob
    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String answer;

}
