package com.capstone.livenote.recording;

import com.capstone.livenote.global.stomp.StreamGateway;
import com.capstone.livenote.recording.RecordingStateStore.TimeOffset;
import com.capstone.livenote.global.redis.RedisKeys;
import com.capstone.livenote.global.redis.RedisLock;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * 녹음에서 확정된 전사를 저장하고, 섹션 배정과 요약 요청으로 이어지게 한다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class TranscriptService {

    private final TranscriptRepository transcriptRepository;
    private final StreamGateway streamGateway;
    private final SectionAggregationService sectionAggregationService;
    private final RecordingStateStore stateStore;
    private final RedisLock redisLock;

    /**
     * 확정된 전사 한 문장을 강의 전체 기준 시각으로 바꿔 저장하고 실시간으로 전송한다.
     *
     * 저장 전에 섹션을 정하고, 저장 후 섹션 길이에 따라 요약을 요청한다. 저장 후의 요약 요청 단계가 실패하면 로그로만 남긴다.
     * 같은 강의의 전사는 서버 여러 대에 걸쳐 한 번에 하나씩 처리한다. 섹션 상태를 읽고 고쳐 쓰는 사이에
     * 다른 전사가 끼어들면 섹션 번호가 어긋나기 때문이다.
     *
     * @param lectureId 강의 ID
     * @param startSec 전사 시작 시각(초). 녹음이 다시 시작돼 이전보다 앞선 값이 오면 이어지도록 보정함
     * @param endSec 전사 끝 시각(초)
     * @param text 전사 문장
     * @return 저장한 전사
     */
    public TranscriptResponseDto saveFromStt(Long lectureId, int startSec, int endSec, String text) {
        return redisLock.call(RedisKeys.transcriptLock(lectureId),
                () -> saveLocked(lectureId, startSec, endSec, text));
    }

    private TranscriptResponseDto saveLocked(Long lectureId, int startSec, int endSec, String text) {
        int offset = resolveOffset(lectureId, startSec);
        int adjustedStart = startSec + offset;
        int adjustedEnd = endSec + offset;

        int sectionIndex = sectionAggregationService.assignSection(lectureId, adjustedStart, adjustedEnd);

        log.info("[TranscriptService] Saving transcript: lectureId={} startSec={} endSec={} sectionIndex={}",
                lectureId, adjustedStart, adjustedEnd, sectionIndex);

        Transcript saved = transcriptRepository.save(
                Transcript.builder()
                        .lectureId(lectureId)
                        .sectionIndex(sectionIndex)
                        .startSec(adjustedStart)
                        .endSec(adjustedEnd)
                        .text(text)
                        .build()
        );

        TranscriptResponseDto dto = TranscriptResponseDto.from(saved);
        streamGateway.sendTranscript(lectureId, dto, true);

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
