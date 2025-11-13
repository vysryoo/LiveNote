package com.capstone.livenote.application.audio.service;

import com.capstone.livenote.application.ai.client.AiClient;
import com.capstone.livenote.application.audio.storage.AudioStorage;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

@Service
@RequiredArgsConstructor
public class AudioIngestService {

    private final AudioStorage storage;   // 파일 저장 (local)
    private final AiClient aiClient;      // AI 서버로 전달

    @Transactional
    public void uploadChunk(Long lectureId, int chunkSeq, int startSec, int endSec, MultipartFile file)
            throws IOException {

        // 단순히 저장만 하고 AI 서버로 보냄
        var uri = storage.save(lectureId, chunkSeq, file.getBytes());
        System.out.println("Chunk uploaded: lecture=" + lectureId + " seq=" + chunkSeq + " file=" + uri);

        // 데모 단계에서 AI 서버가 없을때 주석 처리예정
        aiClient.sendChunk(lectureId, chunkSeq, startSec, endSec, uri);
    }

    @Transactional
    public void markComplete(Long lectureId) {
        System.out.println("Lecture upload complete: lecture=" + lectureId);

        aiClient.notifyComplete(lectureId);
    }
}
