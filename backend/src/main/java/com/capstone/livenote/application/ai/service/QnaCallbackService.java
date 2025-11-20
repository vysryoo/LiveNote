package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class QnaCallbackService {

    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;

    @Transactional
    public void handleQnaCallback(QnaCallbackDto dto) {

        List<Qna> saved = dto.getQnaList().stream()
                .map(item -> qnaRepository.save(
                        Qna.builder()
                                .lectureId(dto.getLectureId())
                                .summaryId(dto.getSummaryId())
                                .sectionIndex(dto.getSectionIndex())
                                .type(resolveType(item.getType()))
                                .question(item.getQuestion())
                                .answer(item.getAnswer())
                                .build()
                )).toList();

        List<QnaResponseDto> items = saved.stream()
                .map(QnaResponseDto::from)
                .toList();

        streamGateway.sendQna(dto.getLectureId(), dto.getSectionIndex(), items);
    }

    private Qna.Type resolveType(String raw) {
        if (raw == null) {
            return Qna.Type.CONCEPT;
        }
        return switch (raw.trim().toUpperCase()) {
            case "APPLICATION", "응용" -> Qna.Type.APPLICATION;
            case "ADVANCED", "심화" -> Qna.Type.ADVANCED;
            case "COMPARISON", "비교" -> Qna.Type.COMPARISON;
            case "CONCEPT", "개념" -> Qna.Type.CONCEPT;
            default -> Qna.Type.CONCEPT;
        };
    }
}
