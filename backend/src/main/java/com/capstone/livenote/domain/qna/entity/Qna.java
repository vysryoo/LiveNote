package com.capstone.livenote.domain.qna.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "qna",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_qna_card", columnNames = {"lecture_id", "section_index", "card_id"})
        })
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Qna {

    public enum Type {
        CONCEPT, APPLICATION, ADVANCED, COMPARISON;

        /**
         * AI 서버가 보낸 질문 유형을 변환한다. 영문과 한글 이름을 모두 받는다.
         *
         * @param raw 질문 유형. null 허용
         * @return 질문 유형. 알 수 없는 값이거나 null이면 CONCEPT
         */
        public static Type from(String raw) {
            if (raw == null) {
                return CONCEPT;
            }
            return switch (raw.trim().toUpperCase()) {
                case "APPLICATION", "응용" -> APPLICATION;
                case "ADVANCED", "심화" -> ADVANCED;
                case "COMPARISON", "비교" -> COMPARISON;
                default -> CONCEPT;
            };
        }
    }

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "lecture_id", nullable = false)
    private Long lectureId;

    @Column(name = "summary_id")
    private Long summaryId;

    @Column(nullable = false)
    private Integer sectionIndex;

    @Column(name = "card_id", length = 128, nullable = false)
    private String cardId;

    @Enumerated(EnumType.STRING)
    private Type type;

    @Column(nullable = false)
    private String question;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String answer;

}
