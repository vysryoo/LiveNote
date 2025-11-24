package com.livenote.controller;

import com.livenote.dto.*;
import com.livenote.service.LectureService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/lectures")
@RequiredArgsConstructor
public class LectureController {
    private final LectureService lectureService;

    @GetMapping
    public ResponseEntity<List<LectureDto>> getLectures() {
        return ResponseEntity.ok(lectureService.getLectures());
    }

    @GetMapping("/{id}")
    public ResponseEntity<SessionDetailResponse> getLecture(@PathVariable Long id) {
        return ResponseEntity.ok(lectureService.getLecture(id));
    }

    @PostMapping
    public ResponseEntity<LectureDto> createLecture(
            @RequestPart(value = "title") String title,
            @RequestPart(value = "subject", required = false) String subject,
            @RequestPart(value = "sttLanguage") String sttLanguage,
            @RequestPart(value = "files", required = false) List<MultipartFile> files) {
        CreateLectureRequest request = new CreateLectureRequest();
        request.setTitle(title);
        request.setSubject(subject);
        request.setSttLanguage(sttLanguage);
        return ResponseEntity.ok(lectureService.createLecture(request, files));
    }

    @PostMapping(consumes = "application/json")
    public ResponseEntity<LectureDto> createLectureJson(@Valid @RequestBody CreateLectureRequest request) {
        return ResponseEntity.ok(lectureService.createLecture(request, null));
    }

    @PatchMapping("/{id}/title")
    public ResponseEntity<LectureDto> updateLectureTitle(
            @PathVariable Long id,
            @Valid @RequestBody UpdateLectureTitleRequest request) {
        return ResponseEntity.ok(lectureService.updateLectureTitle(id, request));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteLecture(@PathVariable Long id) {
        lectureService.deleteLecture(id);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/end")
    public ResponseEntity<LectureDto> endLecture(
            @PathVariable Long id,
            @RequestBody(required = false) UpdateLectureTitleRequest request) {
        return ResponseEntity.ok(lectureService.endLecture(id, request));
    }
}

