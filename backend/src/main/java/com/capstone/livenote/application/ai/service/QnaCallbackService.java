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
                                .sectionIndex(dto.getSectionIndex())
                                .type(Qna.Type.valueOf(item.getType().toUpperCase()))
                                .question(item.getQuestion())
                                .answer(item.getAnswer())
                                .build()
                )).toList();

        List<QnaResponseDto> items = saved.stream()
                .map(QnaResponseDto::from)
                .toList();

        streamGateway.sendQna(dto.getLectureId(), dto.getSectionIndex(), items);
    }
}
