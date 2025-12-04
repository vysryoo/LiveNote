package com.capstone.livenote.domain.resource.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.fasterxml.jackson.databind.JsonNode;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "resources",
        indexes = {@Index(name="idx_resources_summary", columnList = "summary_id")},
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_resource_card", columnNames = {"lecture_id", "section_index", "card_id"})
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Resource {

    public enum Type {
        PAPER, WIKI, VIDEO, BLOG, GOOGLE, YOUTUBE;

        public static Type fromString(String value) {
            if (value == null) {
                throw new IllegalArgumentException("type is required");
            }
            String normalized = value.trim().toUpperCase();
            return switch (normalized) {
                case "OPENALEX" -> PAPER;
                case "YOUTUBE" -> VIDEO;
                case "WIKIPEDIA" -> WIKI;
                case "WEB", "GOOGLE" -> GOOGLE;
                default -> Type.valueOf(normalized);
            };
        }
    }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "summary_id")
    private Long summaryId;


    @Column(name = "user_id", nullable = true)
    private Long userId;

    @Column(name = "card_id", length = 128, nullable = false)
    private String cardId;

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

    @Lob
    private String reason;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "json")
    private JsonNode detail;
}
