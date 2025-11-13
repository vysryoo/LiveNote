package com.capstone.livenote.domain.transcript.service;

import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.summary.service.SummaryService;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TranscriptService {
    private final TranscriptRepository transcriptRepository;
    private final SummaryService summaryService; // 30초 요약 업서트용
    private final StreamGateway streamGateway;

    @Transactional(readOnly = true)
    public List<Transcript> findSince(Long lectureId, Integer sinceSec){
        if (sinceSec == null) {
            return transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId);
        }
        return transcriptRepository.findByLectureIdAndStartSecGreaterThanOrderByStartSecAsc(lectureId, sinceSec);
    }


    /**
     * STT 콜백/인제스트 저장 (sectionIndex 자동 계산 + 요약 트리거 + WS 브로드캐스트)
     */
    @Transactional
    public void saveFromStt(Long lectureId, Integer startSec, Integer endSec, String text) {
        int sectionIndex = Math.floorDiv(startSec, 30);

        Transcript saved = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .startSec(startSec)
                        .endSec(endSec)
                        .text(text)
                        .build()
        );

        // 해당 30초 윈도우 요약 멱등 업서트
        summaryService.summarizeWindow(lectureId, sectionIndex * 30, (sectionIndex + 1) * 30);

        // 프론트로 실시간 전송
        streamGateway.sendTranscript(
                lectureId,
                new TranscriptResponseDto(
                        saved.getId(),
                        saved.getLectureId(),
                        saved.getSectionIndex(),
                        saved.getStartSec(),
                        saved.getEndSec(),
                        saved.getText()
                ),
                true
        );

    }
}
