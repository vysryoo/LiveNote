package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
@Slf4j
public class QnaCallbackService {

    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;

    @Value("${app.streaming.chunk-size:40}")
    private int streamChunk;

    @Value("${app.streaming.delay-ms:50}")
    private long streamDelayMs;

    @Transactional
    public void handleQnaCallback(QnaCallbackDto dto) {
        Object lock = lockOf(dto.getLectureId(), dto.getSectionIndex());
        synchronized (lock) {

            log.info("QnA callback: lectureId={} section={} summaryId={} size={}",
                    dto.getLectureId(), dto.getSectionIndex(), dto.getSummaryId(),
                    dto.getQnaList() == null ? 0 : dto.getQnaList().size());

            if (dto.getQnaList() == null || dto.getQnaList().isEmpty()) {
                log.info("QnA callback skipped: empty payload");
                return;
            }

            List<Qna> existing = qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                    dto.getLectureId(), dto.getSectionIndex()
            );

            Set<String> signature = new HashSet<>();
            existing.forEach(q -> signature.add(sig(q.getQuestion(), q.getAnswer())));

            int cursor = nextCursor(existing);

            for (var item : dto.getQnaList()) {
                String sig = sig(item.getQuestion(), item.getAnswer());
                if (signature.contains(sig)) {
                    log.debug("Skipping duplicate QnA for lecture {} section {}: {}", dto.getLectureId(), dto.getSectionIndex(), item.getQuestion());
                    continue;
                }
                String cardId = CardIdHelper.buildCardId("qna", dto.getLectureId(), dto.getSectionIndex(), cursor++);
                if (qnaRepository.existsByLectureIdAndSectionIndexAndCardId(dto.getLectureId(), dto.getSectionIndex(), cardId)) {
                    continue;
                }

                Qna saved = qnaRepository.save(
                        Qna.builder()
                                .lectureId(dto.getLectureId())
                                .summaryId((dto.getSummaryId() == null || dto.getSummaryId() == 0L) ? null : dto.getSummaryId())
                                .sectionIndex(dto.getSectionIndex())
                                .cardId(cardId)
                                .type(resolveType(item.getType()))
                                .question(item.getQuestion())
                                .answer(item.getAnswer())
                                .build()
                );
                signature.add(sig);

                // 1) 토큰 스트리밍
                streamTokens(
                        dto.getLectureId(),
                        cardId,
                        item.getQuestion(),
                        item.getAnswer()
                );
                // 2) 완료 스트리밍 (최종 데이터)
                streamGateway.sendStreamToken(
                        dto.getLectureId(),
                        "qna_stream",
                        cardId,
                        null,
                        true,
                        QnaResponseDto.from(saved),
                        null,
                        null
                );
            }

            // 2. 전체 조회 (해당 섹션의 모든 QnA 조회) -> 프론트에 누적된 데이터 전송
            List<Qna> allQnas = qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                    dto.getLectureId(), dto.getSectionIndex()
            );

            // 3. DTO 변환 및 전송
            List<QnaResponseDto> items = allQnas.stream()
                    .map(QnaResponseDto::from)
                    .toList();

            streamGateway.sendQna(dto.getLectureId(), dto.getSectionIndex(), items);
        }
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

    private String sig(String question, String answer) {
        return (question == null ? "" : question.trim()) + "|" + (answer == null ? "" : answer.trim());
    }

    private void streamTokens(Long lectureId, String cardId, String title, String content) {
        if (content == null || content.isBlank()) {
            return;
        }
        String text = content.trim();
        int chunk = Math.max(1, streamChunk);
        for (int i = 0; i < text.length(); i += chunk) {
            int end = Math.min(text.length(), i + chunk);
            String token = text.substring(i, end);
            streamGateway.sendStreamToken(
                    lectureId,
                    "qna_stream",
                    cardId,
                    token,
                    false,
                    null,
                    title,
                    null
            );
            try {
                Thread.sleep(streamDelayMs);
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    private int nextCursor(List<Qna> existing) {
        int maxIdx = existing.stream()
                .mapToInt(q -> CardIdHelper.extractCardIndex(q.getCardId(), CardIdHelper.CARD_INDEX_OFFSET - 1))
                .max()
                .orElse(CardIdHelper.CARD_INDEX_OFFSET - 1);
        return maxIdx + 1;
    }

    private Object lockOf(Long lectureId, Integer sectionIndex) {
        String key = lectureId + "-" + sectionIndex;
        return LOCKS.computeIfAbsent(key, k -> new Object());
    }

    private static final ConcurrentHashMap<String, Object> LOCKS = new ConcurrentHashMap<>();
}
