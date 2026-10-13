package com.capstone.livenote.application.test; // 패키지명 확인

import com.capstone.livenote.domain.transcript.service.TranscriptService;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Profile;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

// 실제 강의에 가짜 데이터를 넣는 개발용 API라 dev 프로필로 실행할 때만 등록
@Profile("dev")
@RestController
@RequestMapping("/test")
@RequiredArgsConstructor
@Slf4j
public class TestController {

    private final TranscriptService transcriptService;

    // 30초 분량의 전사 데이터를 강제로 밀어넣는 시뮬레이션
    @PostMapping("/{lectureId}/simulate")
    public String simulate(@PathVariable Long lectureId) throws InterruptedException {
        log.info("🚀 [Simulation] Starting transcript simulation for lectureId={}", lectureId);

        // 0~5초
        transcriptService.saveFromStt(lectureId, 0, 5, "자, 오늘은 자료구조에 대해 배웁니다.");
        Thread.sleep(100); // 실제처럼 약간의 텀을 둠

        // 5~10초
        transcriptService.saveFromStt(lectureId, 5, 10, "스택과 큐의 차이점을 아는 것이 중요합니다.");
        Thread.sleep(100);

        // 10~15초 (여기서 15초 Partial 요약 트리거!)
        log.info("⏳ [Simulation] Approaching 15s mark...");
        transcriptService.saveFromStt(lectureId, 10, 15, "스택은 LIFO, 즉 후입선출 구조를 가집니다.");
        Thread.sleep(100);

        // 15~20초
        transcriptService.saveFromStt(lectureId, 15, 20, "반면에 큐는 FIFO, 선입선출 구조입니다.");
        Thread.sleep(100);

        // 20~25초
        transcriptService.saveFromStt(lectureId, 20, 25, "이 두 가지는 알고리즘에서 매우 자주 사용됩니다.");
        Thread.sleep(100);

        // 25~30초 (여기서 30초 Final 요약 트리거!)
        log.info("⏳ [Simulation] Approaching 30s mark...");
        transcriptService.saveFromStt(lectureId, 25, 30, "이것으로 첫 번째 섹션의 기본 개념 설명을 마칩니다.");

        return "Simulation completed! Check your server logs for [SectionAgg] messages.";
    }
}