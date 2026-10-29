package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.global.redis.RedisLock;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
@Slf4j
public class QnaCallbackService {

    private final QnaRepository qnaRepository;
    private final StreamGateway streamGateway;
    private final RedisLock redisLock;
    private final TransactionTemplate transactionTemplate;

    /**
     * AI 서버가 보낸 카드를 저장하고 실시간으로 전송한다.
     *
     * 같은 섹션의 콜백은 서버 여러 대에 걸쳐 하나씩 처리한다. 카드 번호를 기존 카드의 최댓값 다음으로 정하므로
     * 동시에 처리하면 번호가 겹친다. 잠금은 DB 저장이 확정된 뒤에 푼다.
     *
     * @param dto AI 서버 콜백 본문
     * @throws IllegalStateException 잠금을 얻지 못한 경우
     */
    public void handleQnaCallback(QnaCallbackDto dto) {
        String lockKey = "livenote:lock:lecture:" + dto.getLectureId() + ":section:" + dto.getSectionIndex() + ":qna";
        redisLock.run(lockKey, () -> transactionTemplate.executeWithoutResult(status -> saveCards(dto)));
    }

    private void saveCards(QnaCallbackDto dto) {
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

            // 완성된 카드를 즉시 전송. 글자가 써지는 연출은 프론트엔드가 담당
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

    private int nextCursor(List<Qna> existing) {
        int maxIdx = existing.stream()
                .mapToInt(q -> CardIdHelper.extractCardIndex(q.getCardId(), CardIdHelper.CARD_INDEX_OFFSET - 1))
                .max()
                .orElse(CardIdHelper.CARD_INDEX_OFFSET - 1);
        return maxIdx + 1;
    }
}
