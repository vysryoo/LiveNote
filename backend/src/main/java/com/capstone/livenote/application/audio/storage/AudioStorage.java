package com.capstone.livenote.application.audio.storage;

import java.io.IOException;

public interface AudioStorage {
    String save(Long lectureId, int chunkSeq, byte[] bytes) throws IOException, IOException;
}
