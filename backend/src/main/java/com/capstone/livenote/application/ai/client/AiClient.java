package com.capstone.livenote.application.ai.client;

public interface AiClient {
    void sendChunk(Long lectureId, int chunkSeq, int startSec, int endSec, String fileUri);
    void notifyComplete(Long lectureId);
    void requestResourcesAndQna(Long lectureId, Long summaryId, Integer sectionIndex); // 선택
}


