package com.capstone.livenote.domain.resource.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.summary.entity.Summary;
import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "resources",
        indexes = {@Index(name="idx_resources_summary", columnList = "summary_id")})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Resource {

    public enum Type { PAPER, WIKI, VIDEO, BLOG }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "summary_id")
    private Long summaryId;


    @Column(name = "user_id", nullable = false)
    private Long userId;


    @Column(nullable = false)
    private Integer sectionIndex;

    @Enumerated(EnumType.STRING) @Column(nullable = false)
    private Type type;

    @Column(nullable = false)
    private String title;

    @Lob
    private String text;

    @Column(nullable = false, length = 2048)
    private String url;

    private String thumbnail;

    private Double score;
}
