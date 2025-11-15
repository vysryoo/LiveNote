package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * QnA 콜백 처리 서비스
 */
@Service
@RequiredArgsConstructor
public class QnaCallbackService {

    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;

    @Transactional
    public void saveQna(QnaCallbackDto dto) {
        if (dto.getQnaList() == null || dto.getQnaList().isEmpty()) {
            return;
        }

        for (var item : dto.getQnaList()) {
            Qna saved = qnaRepository.save(Qna.builder()
                    .lectureId(dto.getLectureId())
                    .sectionIndex(dto.getSectionIndex())
                    .type(Qna.Type.valueOf(item.getType().toUpperCase()))
                    .question(item.getQuestion())
                    .answer(item.getAnswer())
                    .build());

            // WebSocket 전송
            Map<String, Object> qnaData = new HashMap<>();
            qnaData.put("id", saved.getId());
            qnaData.put("sectionIndex", saved.getSectionIndex());
            qnaData.put("type", saved.getType().name().toLowerCase());
            qnaData.put("question", saved.getQuestion());
            qnaData.put("answer", saved.getAnswer());

            streamGateway.sendQna(dto.getLectureId(), qnaData);
        }

        System.out.println("[QnaCallback] Saved " + dto.getQnaList().size() +
                " QnAs for section " + dto.getSectionIndex());
    }
}