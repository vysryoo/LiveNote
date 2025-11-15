package com.capstone.livenote.application.audio.service;

import com.capstone.livenote.application.audio.storage.AudioStorage;
import com.capstone.livenote.application.openai.service.OpenAiSttService;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.transcript.service.TranscriptService;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

/**
 * 오디오 청크 처리 서비스
 *
 * 플로우:
 * 1. 오디오 파일 저장 (로컬)
 * 2. OpenAI Whisper로 STT 처리
 * 3. Transcript 저장 (TranscriptService 위임)
 */
@Service
@RequiredArgsConstructor
public class AudioIngestService {

    private final AudioStorage storage;
    private final OpenAiSttService sttService;
    private final TranscriptService transcriptService;
    private final LectureRepository lectureRepository;

    /**
     * 오디오 청크 업로드 및 STT 처리
     */
    @Transactional
    public void uploadChunk(Long lectureId, int chunkSeq, int startSec, int endSec, MultipartFile file)
            throws IOException {

        // 1) 강의 존재 확인
        Lecture lecture = lectureRepository.findById(lectureId)
                .orElseThrow(() -> new IllegalArgumentException("강의를 찾을 수 없습니다: " + lectureId));

        // 2) 오디오 파일 저장
        String uri = storage.save(lectureId, chunkSeq, file.getBytes());
        System.out.println("[AudioIngest] Chunk saved: lecture=" + lectureId +
                " seq=" + chunkSeq + " file=" + uri);

        // 3) OpenAI Whisper STT 호출
        String filename = lectureId + "_" + chunkSeq + ".webm";
        String transcriptText = sttService.transcribe(
                file.getBytes(),
                filename,
                lecture.getSttLanguage()
        );

        System.out.println("[AudioIngest] STT completed: " +
                transcriptText.substring(0, Math.min(50, transcriptText.length())) + "...");

        // 4) Transcript 저장 + 요약 트리거 + WebSocket 전송
        transcriptService.saveFromStt(lectureId, startSec, endSec, transcriptText);
    }

    /**
     * 강의 녹음 완료 처리
     */
    @Transactional
    public void markComplete(Long lectureId) {
        System.out.println("[AudioIngest] Lecture upload complete: lecture=" + lectureId);

        lectureRepository.findById(lectureId).ifPresent(lecture -> {
            lecture.setStatus(Lecture.Status.COMPLETED);
            lectureRepository.save(lecture);
        });
    }
}