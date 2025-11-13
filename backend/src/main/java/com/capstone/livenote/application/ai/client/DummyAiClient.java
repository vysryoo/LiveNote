package com.capstone.livenote.application.ai.client;

import org.springframework.stereotype.Component;

// Ai 서버 연결 전 더미
@Component
public class DummyAiClient implements AiClient {
    @Override
    public void sendChunk(Long lectureId, int chunkSeq, int startSec, int endSec, String fileUri) {
        System.out.println("[DummyAiClient] sendChunk called: " + fileUri);
    }

    @Override
    public void notifyComplete(Long lectureId) {
        System.out.println("[DummyAiClient] notifyComplete called: lecture=" + lectureId);
    }

    @Override
    public void requestResourcesAndQna(Long lectureId, Long summaryId, Integer sectionIndex) {

    }
}