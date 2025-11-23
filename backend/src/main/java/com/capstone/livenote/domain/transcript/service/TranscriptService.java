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
     * 1. 현재 강의의 최대 sectionIndex 조회
     * 2. Transcript 저장 (sectionIndex 계산)
     * 3. (섹션/요약/AI 요청 로직) 트리거
     * 4. 저장된 내용을 DTO로 반환 → 호출한 쪽에서 WebSocket push
     */
    @Transactional
    public TranscriptResponseDto saveFromStt(Long lectureId, int startSec, int endSec, String text) {
        // 1) 현재 강의의 최대 sectionIndex 조회 (이전에 저장된 전사가 있는지 확인)
        Integer maxSectionIndex = transcriptRepository.findMaxSectionIndexByLectureId(lectureId);
        if (maxSectionIndex == null) {
            maxSectionIndex = -1; // 처음 전사인 경우
        }
        
        // 2) sectionIndex 계산: 30초 단위 섹션
        int sectionIndex = startSec / 30;
        
        // 만약 계산된 sectionIndex가 기존 최대값보다 작으면, 기존 최대값 + 1로 설정
        // (강의 재개 시 시간이 리셋되는 경우 대비)
        if (sectionIndex <= maxSectionIndex) {
            sectionIndex = maxSectionIndex + 1;
        }
        
        log.info("[TranscriptService] Saving transcript: lectureId={} startSec={} endSec={} sectionIndex={} (maxExisting={})",
                lectureId, startSec, endSec, sectionIndex, maxSectionIndex);
        
        // 3) Transcript 엔티티 저장
        Transcript t = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .startSec(startSec)
                        .endSec(endSec)
                        .text(text)
                        .build()
        );

        // 4) 섹션/요약/AI 요청 로직 트리거
        sectionAggregationService.onNewTranscript(lectureId, sectionIndex, startSec, endSec, text);

        // 5) 호출한 쪽(AudioWebSocketHandler 등)에서 WebSocket 전송하도록 DTO 반환
        return TranscriptResponseDto.from(t);
    }
}
