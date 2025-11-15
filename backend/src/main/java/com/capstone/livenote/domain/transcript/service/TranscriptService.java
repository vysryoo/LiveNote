package com.capstone.livenote.domain.transcript.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TranscriptService {
    private final TranscriptRepository transcriptRepository;
    private final SummaryService summaryService; // 30초 요약 업서트용
    //private final StreamGateway streamGateway;

    @Transactional(readOnly = true)
    public List<Transcript> findSince(Long lectureId, Integer sinceSec){
        if (sinceSec == null) {
            return transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId);
        }
        return transcriptRepository.findByLectureIdAndStartSecGreaterThanOrderByStartSecAsc(lectureId, sinceSec);
    }


    /**
     * STT 결과 저장 및 후속 처리
     *
     * 플로우:
     * 1. Transcript 저장
     * 2. WebSocket으로 실시간 전송
     * 3. 30초 윈도우 요약 트리거
     */
    @Transactional
    public void saveFromStt(Long lectureId, Integer startSec, Integer endSec, String text) {
        int sectionIndex = Math.floorDiv(startSec, 30);

        // 1) Transcript 저장
        Transcript saved = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .startSec(startSec)
                        .endSec(endSec)
                        .text(text)
                        .build()
        );

        System.out.println("[TranscriptService] Saved transcript: id=" + saved.getId() +
                " section=" + sectionIndex);

        // 2) WebSocket으로 실시간 전송
        Map<String, Object> transcriptData = new HashMap<>();
        transcriptData.put("id", saved.getId());
        transcriptData.put("lectureId", saved.getLectureId());
        transcriptData.put("sectionIndex", saved.getSectionIndex());
        transcriptData.put("startSec", saved.getStartSec());
        transcriptData.put("endSec", saved.getEndSec());
        transcriptData.put("text", saved.getText());

        //streamGateway.sendTranscript(lectureId, transcriptData, true);

        // 3) 30초 윈도우 요약 생성 트리거
        int windowStart = sectionIndex * 30;
        int windowEnd = (sectionIndex + 1) * 30;
        summaryService.summarizeWindow(lectureId, windowStart, windowEnd);
    }
}
