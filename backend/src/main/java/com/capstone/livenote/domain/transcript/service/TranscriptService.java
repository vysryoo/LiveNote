package com.capstone.livenote.domain.transcript.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import com.capstone.livenote.application.ai.service.SectionAggregationService;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

// STT 저장, 섹션/요약 트리거만
@Service
@RequiredArgsConstructor
@Slf4j
public class TranscriptService {

    private final TranscriptRepository transcriptRepository;
    // private final SummaryService summaryService;      // 예전 30초 요약용 (사용 안 하면 삭제해도 됨)
    private final SectionAggregationService sectionAggregationService;

    // 재시작 감지용: 강의별 raw startSec 오프셋
    private final Map<Long, Integer> baseOffsets = new HashMap<>();
    private final Map<Long, Integer> lastRawStarts = new HashMap<>();

    @Transactional(readOnly = true)
    public List<Transcript> findSince(Long lectureId, Integer sinceSec) {
        log.info("📂 [DB READ] Fetching transcripts: lectureId={} sinceSec={}", lectureId, sinceSec);
        List<Transcript> result;
        if (sinceSec == null) {
            result = transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId);
        } else {
            result = transcriptRepository.findByLectureIdAndStartSecGreaterThanOrderByStartSecAsc(lectureId, sinceSec);
        }
        log.info("✅ [DB READ] Loaded {} transcripts for lectureId={}", result.size(), lectureId);
        return result;
    }

    /**
     * STT 결과 저장 및 후속 처리
     * 플로우:
     * 1. 30초 단위 sectionIndex 계산
     * 2. Transcript 저장
     * 3. (섹션/요약/AI 요청 로직) 트리거
     * 4. 저장된 내용을 DTO로 반환 → 호출한 쪽에서 WebSocket push
     */
    @Transactional
    public TranscriptResponseDto saveFromStt(Long lectureId, int startSec, int endSec, String text) {
        // 1) 강의별 오프셋 계산 (이전 기록이 있는데 클라이언트 startSec이 리셋된 경우 이어붙이기)
        int offset = resolveOffset(lectureId, startSec);
        int adjustedStart = startSec + offset;
        int adjustedEnd = endSec + offset;

        // 2) sectionIndex 계산: 30초 단위 섹션 (연속 청크가 동일 섹션에 쌓이도록 고정)
        int sectionIndex = adjustedStart / 30;

        log.info("[TranscriptService] Saving transcript: lectureId={} startSec={} endSec={} sectionIndex={}",
                lectureId, adjustedStart, adjustedEnd, sectionIndex);

        // 3) Transcript 엔터티 저장
        Transcript t = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .startSec(adjustedStart)
                        .endSec(adjustedEnd)
                        .text(text)
                        .build()
        );

        // 4) 섹션/요약/AI 요청 로직 트리거
        sectionAggregationService.onNewTranscript(lectureId, sectionIndex, adjustedStart, adjustedEnd, text);

        // 5) 호출한 쪽(AudioWebSocketHandler 등)에서 WebSocket 전송하도록 DTO 반환
        return TranscriptResponseDto.from(t);
    }

    /**
     * 오디오 재시작 시 클라이언트 startSec/endSec이 0부터 리셋되는 경우가 있으므로,
     * DB에 저장된 마지막 endSec를 기준으로 offset을 더해 시간/섹션이 겹치지 않도록 한다.
     * 단, 정상 진행 중(연속 청크)에는 offset=0을 유지한다.
     */
    private int resolveOffset(Long lectureId, int rawStartSec) {
        Integer lastRaw = lastRawStarts.get(lectureId);
        Integer base = baseOffsets.get(lectureId);

        if (lastRaw == null) {
            // 첫 청크: 기존 DB 데이터가 있으면 이어붙이기 판단
            Integer maxEndSec = transcriptRepository.findMaxEndSecByLectureId(lectureId);
            if (maxEndSec != null && rawStartSec < maxEndSec) {
                base = maxEndSec;
                baseOffsets.put(lectureId, base);
                log.info("🔄 [TranscriptService] Detected resume: lectureId={} baseOffset={}", lectureId, base);
            } else {
                base = 0;
                baseOffsets.put(lectureId, 0);
            }
        } else {
            // 연속 청크인지 확인: raw start가 이전보다 작아지면 재시작으로 판단
            if (rawStartSec < lastRaw) {
                Integer maxEndSec = transcriptRepository.findMaxEndSecByLectureId(lectureId);
                if (maxEndSec != null) {
                    base = maxEndSec;
                    baseOffsets.put(lectureId, base);
                    log.info("🔄 [TranscriptService] Detected restart mid-session: lectureId={} baseOffset={}", lectureId, base);
                }
            } else if (base == null) {
                baseOffsets.put(lectureId, 0);
                base = 0;
            }
        }

        lastRawStarts.put(lectureId, rawStartSec);
        return base != null ? base : 0;
    }
}
