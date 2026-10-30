package com.capstone.livenote.recording;

import com.capstone.livenote.global.stomp.StreamGateway;
import com.capstone.livenote.recording.RecordingStateStore.TimeOffset;
import com.capstone.livenote.global.redis.RedisKeys;
import com.capstone.livenote.global.redis.RedisLock;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;

// STT 저장, 섹션/요약 트리거만
@Service
@RequiredArgsConstructor
@Slf4j
public class TranscriptService {

    private final TranscriptRepository transcriptRepository;
    private final StreamGateway streamGateway; // 실시간 전송
    private final SectionAggregationService sectionAggregationService;
    private final RecordingStateStore stateStore;
    private final RedisLock redisLock;

    /**
     * STT 결과 저장 및 후속 처리
     * 플로우:
     * 1. 30초 단위 sectionIndex 계산
     * 2. Transcript 저장
     * 3. (섹션/요약/AI 요청 로직) 트리거
     * 4. 저장된 내용을 DTO로 반환 → 호출한 쪽에서 WebSocket push
     *
     * 같은 강의의 전사는 서버 여러 대에 걸쳐 한 번에 하나씩 처리한다. 섹션 상태를 읽고 고쳐 쓰는 사이에
     * 다른 전사가 끼어들면 섹션 번호가 어긋나기 때문이다.
     */
    public TranscriptResponseDto saveFromStt(Long lectureId, int startSec, int endSec, String text) {
        return redisLock.call(RedisKeys.transcriptLock(lectureId),
                () -> saveLocked(lectureId, startSec, endSec, text));
    }

    private TranscriptResponseDto saveLocked(Long lectureId, int startSec, int endSec, String text) {
        // 1) 강의별 오프셋 계산 (이전 기록이 있는데 클라이언트 startSec이 리셋된 경우 이어붙이기)
        int offset = resolveOffset(lectureId, startSec);
        int adjustedStart = startSec + offset;
        int adjustedEnd = endSec + offset;

        // 2) 섹션 배정: 섹션 시작으로부터 30초 이상 지난 전사는 새 섹션
        int sectionIndex = sectionAggregationService.assignSection(lectureId, adjustedStart, adjustedEnd);

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

        // 4) 저장된 전사를 모든 클라이언트에게 실시간 브로드캐스트 (WebSocket)
        TranscriptResponseDto dto = TranscriptResponseDto.from(t);
        streamGateway.sendTranscript(lectureId, dto, true);

        //  5) 섹션 길이 확인 후 요약 요청 (15초/30초 트리거)
        try {
            sectionAggregationService.onTranscriptSaved(lectureId);
        } catch (Exception e) {
            log.error("Failed to aggregate section: {}", e.getMessage(), e);
        }

        return dto;
    }

    /**
     * 오디오 재시작 시 클라이언트 startSec/endSec이 0부터 리셋되는 경우가 있으므로,
     * DB에 저장된 마지막 endSec를 기준으로 offset을 더해 시간/섹션이 겹치지 않도록 한다.
     * 단, 정상 진행 중(연속 청크)에는 offset=0을 유지한다.
     */
    private int resolveOffset(Long lectureId, int rawStartSec) {
        Optional<TimeOffset> saved = stateStore.findOffset(lectureId);
        int base;

        if (saved.isEmpty()) {
            // 첫 청크: 기존 DB 데이터가 있으면 이어붙이기 판단
            Integer maxEndSec = transcriptRepository.findMaxEndSecByLectureId(lectureId);
            if (maxEndSec != null && rawStartSec < maxEndSec) {
                base = maxEndSec;
                log.info("[TranscriptService] Detected resume: lectureId={} baseOffset={}", lectureId, base);
            } else {
                base = 0;
            }
        } else {
            base = saved.get().base();
            // 연속 청크인지 확인: raw start가 이전보다 작아지면 재시작으로 판단
            if (rawStartSec < saved.get().lastRawStart()) {
                Integer maxEndSec = transcriptRepository.findMaxEndSecByLectureId(lectureId);
                if (maxEndSec != null) {
                    base = maxEndSec;
                    log.info("[TranscriptService] Detected restart mid-session: lectureId={} baseOffset={}", lectureId, base);
                }
            }
        }

        stateStore.saveOffset(lectureId, new TimeOffset(base, rawStartSec));
        return base;
    }

}
