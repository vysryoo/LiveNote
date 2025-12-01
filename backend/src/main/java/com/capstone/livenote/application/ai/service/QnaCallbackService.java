package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class QnaCallbackService {

    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;

    @Transactional
    public void handleQnaCallback(QnaCallbackDto dto) {

        log.info("QnA callback: lectureId={} section={} summaryId={} size={}",
                dto.getLectureId(), dto.getSectionIndex(), dto.getSummaryId(),
                dto.getQnaList() == null ? 0 : dto.getQnaList().size());

        // 1. 저장 (이번에 들어온 데이터)
        dto.getQnaList().forEach(item -> qnaRepository.save(
                Qna.builder()
                        .lectureId(dto.getLectureId())
                        .summaryId((dto.getSummaryId() == null || dto.getSummaryId() == 0L) ? null : dto.getSummaryId())
                        .sectionIndex(dto.getSectionIndex())
                        .type(resolveType(item.getType()))
                        .question(item.getQuestion())
                        .answer(item.getAnswer())
                        .build()
        ));

        // 2. 전체 조회 (해당 섹션의 모든 QnA 조회) -> 프론트에 누적된 데이터 전송
        List<Qna> allQnas = qnaRepository.findByLectureIdAndSectionIndex(
                dto.getLectureId(), dto.getSectionIndex()
        );

        // 3. DTO 변환 및 전송
        List<QnaResponseDto> items = allQnas.stream()
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

