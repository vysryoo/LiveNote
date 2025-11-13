package com.capstone.livenote.application.audio.storage;

import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Component
public class LocalAudioStorage implements AudioStorage {
    private final Path root = Paths.get(System.getProperty("user.home"), "livenote-audio");
    @PostConstruct
    void init() throws IOException { Files.createDirectories(root); }
    @Override
    public String save(Long lectureId, int chunkSeq, byte[] bytes) throws IOException {
        Path p = root.resolve(lectureId + "_" + chunkSeq + ".webm");
        Files.write(p, bytes);
        return p.toAbsolutePath().toString();
    }
}

