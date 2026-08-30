package com.capstone.livenote.domain.bookmark.entity;

import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.user.entity.User;
import jakarta.persistence.*;
import lombok.*;

@Entity
// 중복방지 + 검색속도
@Table(
        name = "bookmarks",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_bookmark_user_lecture_section_target",
                columnNames = {"user_id","lecture_id","section_index","target_type","target_id"}
        ),
        indexes = {
                @Index(name="idx_bookmarks_user_lecture", columnList="user_id,lecture_id"),
                @Index(name="idx_bookmarks_user_lecture_section", columnList="user_id,lecture_id,section_index")
        }
)
@Getter @Setter
@NoArgsConstructor @AllArgsConstructor @Builder
public class Bookmark {

    public enum TargetType {
        RESOURCE, QNA;
        public static TargetType fromString(String raw) {
            if (raw == null) return null;
            return switch (raw.trim().toUpperCase()) {
                case "RESOURCE", "RESOURCES" -> TargetType.RESOURCE;
                case "QNA", "Q&A" -> TargetType.QNA;
                default -> null;
            };
        }
    }

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long userId;
    private Long lectureId;
    private Integer sectionIndex;

    @Enumerated(EnumType.STRING)
    private TargetType targetType;

    private Long targetId;
}
