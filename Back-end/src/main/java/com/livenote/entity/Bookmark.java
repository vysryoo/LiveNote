package com.livenote.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "bookmarks")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Bookmark {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "user_id", nullable = false)
    private Long userId;
    
    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;
    
    @Column(name = "section_index", nullable = false)
    private Integer sectionIndex;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "target_type", nullable = false)
    private BookmarkTargetType targetType;
    
    @Column(name = "target_id", nullable = false)
    private Long targetId;
    
    public enum BookmarkTargetType {
        resource, qna
    }
}

