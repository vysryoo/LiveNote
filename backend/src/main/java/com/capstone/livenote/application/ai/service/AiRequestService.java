package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.config.AiHistoryProperties;
import com.capstone.livenote.application.ai.client.RagClient;
import com.capstone.livenote.application.ai.dto.AiRequestPayloads;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.service.LectureService;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.service.QnaService;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.service.ResourceService;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.service.SummaryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import static com.capstone.livenote.application.ai.dto.AiRequestPayloads.PreviousSummaryPayload;
import static com.capstone.livenote.application.ai.dto.AiRequestPayloads.QnaGeneratePayload;
import static com.capstone.livenote.application.ai.dto.AiRequestPayloads.ResourceRecommendPayload;

@Service
@RequiredArgsConstructor
@Slf4j
public class AiRequestService {

    private final RagClient ragClient;
    private final SummaryService summaryService;
    private final ResourceService resourceService;
    private final QnaService qnaService;
    private final LectureService lectureService;
    private final AiHistoryProperties historyProperties;

    // 수동 요청
    public void requestResources(Long lectureId, Integer sectionIndex) {
        Summary summary = summaryService.findByLectureAndSection(lectureId, sectionIndex)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "summary not found"));

        ResourceRecommendPayload payload = buildResourcePayload(
                lectureId,
                summary.getId(),
                sectionIndex,
                summary.getText()
        );
        log.info("🔄 [AI Request] Resource recommendation (Manual): lectureId={} section={}", lectureId, sectionIndex);

        ragClient.requestResourceRecommendation(payload, null);
    }


    // 수동 요
    public void requestQna(Long lectureId, Integer sectionIndex) {
        Summary summary = summaryService.findByLectureAndSection(lectureId, sectionIndex)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "summary not found"));
        Lecture lecture = lectureService.get(lectureId);

        var payload = buildQnaPayload(
                lecture,
                summary.getId(),
                sectionIndex,
                summary.getText()
        );
        log.info("🔄 [AI Request] QnA generation (Manual): lectureId={} section={}", lectureId, sectionIndex);

        ragClient.requestQnaGeneration(payload, null);
    }

    // limit 숫자를 받아서 -> 구체적인 Type List로 변환하여 요청
    public void requestResourcesWithSummary(Long lectureId, Long summaryId, Integer sectionIndex, String sectionSummary, Integer limit) {
        ResourceRecommendPayload payload = buildResourcePayload(lectureId, summaryId, sectionIndex, sectionSummary);

        List<String> types = null;
        if (limit != null && limit == 2) {
            // 15초(Partial)일 때 요청할 2가지 타입 (예: 위키, 비디오)
            types = List.of("WIKI", "VIDEO");
        }
        // limit가 null이면 types도 null -> AI가 알아서 전체(4개) 수행

        ragClient.requestResourceRecommendation(payload, types);
    }

    // limit 숫자를 받아서 -> 구체적인 Type List로 변환하여 요청
    public void requestQnaWithSummary(Long lectureId, Long summaryId, Integer sectionIndex, String sectionSummary, Integer limit) {
        Lecture lecture = lectureService.get(lectureId);
        var payload = buildQnaPayload(lecture, summaryId, sectionIndex, sectionSummary);

        List<String> types = null;
        if (limit != null && limit == 2) {
            // 15초(Partial)일 때 요청할 2가지 타입 (예: 개념, 응용)
            types = List.of("CONCEPT", "APPLICATION");
        }

        ragClient.requestQnaGeneration(payload, types);
    }

    private ResourceRecommendPayload buildResourcePayload(Long lectureId,
                                                          Long summaryId,
                                                          Integer sectionIndex,
                                                          String sectionSummary) {
        if (sectionSummary == null || sectionSummary.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "section summary is required");
        }

        List<PreviousSummaryPayload> previousSummaries = summaryService
                .findPreviousSummaries(lectureId, sectionIndex, historyProperties.getPreviousSummaryCount())
                .stream()
                .map(prev -> PreviousSummaryPayload.builder()
                        .sectionIndex(prev.getSectionIndex())
                        .summary(prev.getText())
                        .build())
                .toList();

        int excludeWindow = historyProperties.getPreviousResourceSections();
        ResourceExcludes excludes = buildResourceExcludes(lectureId, sectionIndex, excludeWindow);

        return ResourceRecommendPayload.builder()
                .lectureId(lectureId)
                .summaryId(summaryId)
                .sectionIndex(sectionIndex)
                .sectionSummary(sectionSummary)
                .previousSummaries(previousSummaries)
                .ytExclude(excludes.yt())
                .wikiExclude(excludes.wiki())
                .paperExclude(excludes.paper())
                .googleExclude(excludes.google())
                .build();
    }

    private QnaGeneratePayload buildQnaPayload(Lecture lecture,
                                               Long summaryId,
                                               Integer sectionIndex,
                                               String sectionSummary) {
        if (sectionSummary == null || sectionSummary.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "section summary is required");
        }

        int historyWindow = historyProperties.getPreviousQaSections();
        List<AiRequestPayloads.PreviousQaPayload> previous = findPreviousQna(
                lecture.getId(),
                sectionIndex,
                historyWindow
        );

        return QnaGeneratePayload.builder()
                .lectureId(lecture.getId())
                .summaryId(summaryId)
                .sectionIndex(sectionIndex)
                .sectionSummary(sectionSummary)
                .subject(lecture.getSubject())
                .previousQa(previous)
                .build();
    }

    private ResourceExcludes buildResourceExcludes(Long lectureId, Integer sectionIndex, int window) {
        if (sectionIndex == null || sectionIndex <= 0 || window <= 0) {
            return new ResourceExcludes(List.of(), List.of(), List.of(), List.of());
        }
        int start = Math.max(0, sectionIndex - window);
        int end = Math.max(-1, sectionIndex - 1);
        if (end < start) {
            return new ResourceExcludes(List.of(), List.of(), List.of(), List.of());
        }

        List<Resource> recent = resourceService.findBySectionRange(lectureId, start, end);

        Set<String> ytTitles = new LinkedHashSet<>();
        Set<String> wikiTitles = new LinkedHashSet<>();
        Set<String> paperIds = new LinkedHashSet<>();
        Set<String> googleUrls = new LinkedHashSet<>();

        for (Resource r : recent) {
            switch (r.getType()) {
                case VIDEO, YOUTUBE -> addIfPresent(ytTitles, r.getTitle());
                case WIKI -> addIfPresent(wikiTitles, r.getTitle());
                case PAPER -> addIfPresent(paperIds, r.getUrl());
                case GOOGLE -> addIfPresent(googleUrls, r.getUrl());
                default -> { }
            }
        }

        return new ResourceExcludes(
                List.copyOf(ytTitles),
                List.copyOf(wikiTitles),
                List.copyOf(paperIds),
                List.copyOf(googleUrls)
        );
    }

    private List<AiRequestPayloads.PreviousQaPayload> findPreviousQna(Long lectureId,
                                                                      Integer sectionIndex,
                                                                      int window) {
        if (sectionIndex == null || sectionIndex <= 0 || window <= 0) {
            return List.of();
        }
        int start = Math.max(0, sectionIndex - window);
        int end = Math.max(-1, sectionIndex - 1);
        if (end < start) {
            return List.of();
        }

        return qnaService.findByLectureWithinSections(lectureId, start, end).stream()
                .map(item -> AiRequestPayloads.PreviousQaPayload.builder()
                        .type(item.getType() != null ? item.getType().name().toLowerCase() : null)
                        .question(item.getQuestion())
                        .answer(item.getAnswer())
                        .build())
                .toList();
    }

    private void addIfPresent(Set<String> bucket, String value) {
        if (value == null) return;
        String trimmed = value.trim();
        if (!trimmed.isEmpty()) {
            bucket.add(trimmed);
        }
    }

    private record ResourceExcludes(List<String> yt, List<String> wiki, List<String> paper, List<String> google) {}



}
