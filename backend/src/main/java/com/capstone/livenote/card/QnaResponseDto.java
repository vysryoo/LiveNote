package com.capstone.livenote.card;

public record QnaResponseDto(
        Long id,
        Long lectureId,
        Long summaryId,
        Integer sectionIndex,
        String cardId,
        String type,
        String question,
        String answer
) {

    public static QnaResponseDto from(Qna q) {
        return new QnaResponseDto(
                q.getId(),
                q.getLectureId(),
                q.getSummaryId(),
                q.getSectionIndex(),
                q.getCardId(),
                q.getType().name().toLowerCase(),
                q.getQuestion(),
                q.getAnswer()
        );
    }
}
