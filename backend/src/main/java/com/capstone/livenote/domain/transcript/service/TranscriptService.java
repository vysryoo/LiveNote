package com.capstone.livenote.domain.transcript.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import com.capstone.livenote.application.ai.service.SectionAggregationService;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

// STT 저장, 섹션/요약 트리거만
@Service
@RequiredArgsConstructor
public class TranscriptService {

    private final TranscriptRepository transcriptRepository;
    // private final SummaryService summaryService;      // 예전 30초 요약용 (사용 안 하면 삭제해도 됨)
    private final SectionAggregationService sectionAggregationService;

    @Transactional(readOnly = true)
    public List<Transcript> findSince(Long lectureId, Integer sinceSec) {
        if (sinceSec == null) {
            return transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId);
        }
        return transcriptRepository.findByLectureIdAndStartSecGreaterThanOrderByStartSecAsc(lectureId, sinceSec);
    }

    /**
     * STT 결과 저장 및 후속 처리
     * 플로우:
     * 1. Transcript 저장
     * 2. (섹션/요약/AI 요청 로직) 트리거
     * 3. 저장된 내용을 DTO로 반환 → 호출한 쪽에서 WebSocket push
     */
    @Transactional
    public TranscriptResponseDto saveFromStt(Long lectureId, int startSec, int endSec, String text) {
        // 1) Transcript 엔티티 저장
        Transcript t = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .startSec(startSec)
                        .endSec(endSec)
                        .text(text)
                        .build()
        );

        // 2) 섹션/요약/AI 요청 로직 트리거
        sectionAggregationService.onNewTranscript(lectureId, startSec, endSec, text);

        // 3) 호출한 쪽(AudioWebSocketHandler 등)에서 WebSocket 전송하도록 DTO 반환
        return TranscriptResponseDto.from(t);
    }
}
