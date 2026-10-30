package com.capstone.livenote.card;

import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.ai.AiHistoryProperties;
import com.capstone.livenote.ai.AiRequestPayloads.PreviousQaPayload;
import com.capstone.livenote.ai.AiRequestPayloads.PreviousSummaryPayload;
import com.capstone.livenote.ai.AiRequestPayloads.QnaGeneratePayload;
import com.capstone.livenote.ai.AiRequestPayloads.ResourceRecommendPayload;
import com.capstone.livenote.global.stomp.StreamGateway;
import com.capstone.livenote.lecture.Lecture;
import com.capstone.livenote.lecture.LectureService;
import com.capstone.livenote.summary.Summary;
import com.capstone.livenote.summary.SummaryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Function;

/**
 * AI 서버에 QnA·자료 카드 생성을 요청한다.
 *
 * 부분 요약이 도착했을 때의 자동 생성과, 분할 화면에서 사용자가 누르는 추가 생성 두 경로가 있다.
 * QnA는 SSE로 받아 바로 중계하고({@link QnaStreamService}), 자료는 AI 서버가 콜백으로 돌려준다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class CardRequestService {

    // 분할 화면에 한 섹션당 보여 주는 카드 수
    private static final int MAX_CARDS_PER_SECTION = 3;
    // 영상은 YouTube 할당량(하루 약 99회)이 작아 사용자가 분할 화면을 열 때의 추가 생성에서만 받음
    private static final List<String> AUTO_RESOURCE_TYPES = List.of("WIKI", "BLOG");
    private static final List<String> AUTO_QNA_TYPES = List.of("CONCEPT", "APPLICATION");
    private static final int SUMMARY_LOOKUP_ATTEMPTS = 6;
    private static final long SUMMARY_LOOKUP_DELAY_MS = 300L;

    private final AiServerClient aiServerClient;
    private final SummaryService summaryService;
    private final ResourceRepository resourceRepository;
    private final QnaRepository qnaRepository;
    private final LectureService lectureService;
    private final AiHistoryProperties historyProperties;
    private final StreamGateway streamGateway;
    private final QnaStreamService qnaStreamService;

    /**
     * 부분 요약을 바탕으로 섹션의 첫 자료 2종과 QnA 2종을 요청한다.
     *
     * 자료와 QnA는 따로 요청하며, 한쪽이 실패해도 다른 쪽은 요청한다. 실패는 로그로만 남긴다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param partialSummary 부분 요약 본문. 아직 저장되지 않은 요약이라 요약 ID 없이 요청함
     */
    public void startAutoCards(Long lectureId, Integer sectionIndex, String partialSummary) {
        log.info("[Card Request] Auto cards: lectureId={} section={}", lectureId, sectionIndex);
        try {
            requestResources(lectureId, sectionIndex, null, partialSummary, AUTO_RESOURCE_TYPES);
        } catch (Exception e) {
            log.error("Auto resource request failed: lectureId={} section={} error={}",
                    lectureId, sectionIndex, e.getMessage());
        }
        try {
            requestQna(lectureId, sectionIndex, null, partialSummary, AUTO_QNA_TYPES);
        } catch (Exception e) {
            log.error("Auto QnA request failed: lectureId={} section={} error={}",
                    lectureId, sectionIndex, e.getMessage());
        }
    }

    /**
     * 분할 화면의 추가 QnA 카드 하나를 요청한다.
     *
     * 섹션에 카드가 이미 3개 이상이면 생성하지 않고 현재 목록을 다시 보내 화면을 맞춘다.
     * 섹션 최종 요약이 아직 저장되지 않았으면 잠시 기다렸다가 다시 찾고, 끝내 없으면 요청하지 않는다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param qnaType 질문 유형. 대소문자 무관
     */
    public void requestExtraQna(Long lectureId, Integer sectionIndex, String qnaType) {
        List<Qna> existing = qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(lectureId, sectionIndex);
        if (existing.size() >= MAX_CARDS_PER_SECTION) {
            log.info("[Card Request] Extra QnA skipped (section full): lectureId={} section={}", lectureId, sectionIndex);
            streamGateway.sendQna(lectureId, sectionIndex, existing.stream().map(QnaResponseDto::from).toList());
            return;
        }
        findSummaryWithRetry(lectureId, sectionIndex).ifPresent(summary ->
                requestQna(lectureId, sectionIndex, summary.getId(), summary.getText(), List.of(qnaType.toUpperCase())));
    }

    /**
     * 분할 화면의 추가 자료 카드 하나를 요청한다. 결과는 AI 서버 콜백으로 도착한다.
     *
     * 섹션에 카드가 이미 3개 이상이면 생성하지 않고 현재 목록을 다시 보내 화면을 맞춘다.
     * 섹션 최종 요약이 아직 저장되지 않았으면 잠시 기다렸다가 다시 찾고, 끝내 없으면 요청하지 않는다.
     *
     * @param lectureId 강의 ID
     * @param sectionIndex 섹션 번호
     * @param resourceType 자료 유형. 대소문자 무관
     */
    public void requestExtraResource(Long lectureId, Integer sectionIndex, String resourceType) {
        List<Resource> existing = resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(lectureId, sectionIndex);
        if (existing.size() >= MAX_CARDS_PER_SECTION) {
            log.info("[Card Request] Extra resource skipped (section full): lectureId={} section={}", lectureId, sectionIndex);
            streamGateway.sendResources(lectureId, sectionIndex, existing.stream().map(ResourceResponseDto::from).toList());
            return;
        }
        findSummaryWithRetry(lectureId, sectionIndex).ifPresent(summary ->
                requestResources(lectureId, sectionIndex, summary.getId(), summary.getText(), List.of(resourceType.toUpperCase())));
    }

    private void requestQna(Long lectureId, Integer sectionIndex, Long summaryId, String sectionSummary, List<String> types) {
        requireSummary(sectionSummary);
        Lecture lecture = lectureService.get(lectureId);
        List<PreviousQaPayload> previousQa = previousSections(sectionIndex, historyProperties.getPreviousQaSections())
                .map(range -> qnaRepository.findByLectureIdAndSectionIndexBetweenOrderBySectionIndexAsc(
                                lectureId, range.start(), range.end()).stream()
                        .map(qna -> PreviousQaPayload.builder()
                                .type(qna.getType() != null ? qna.getType().name().toLowerCase() : null)
                                .question(qna.getQuestion())
                                .answer(qna.getAnswer())
                                .build())
                        .toList())
                .orElse(List.of());

        log.info("[Card Request] QnA: lectureId={} section={} types={}", lectureId, sectionIndex, types);
        qnaStreamService.generate(QnaGeneratePayload.builder()
                .lectureId(lectureId)
                .summaryId(summaryId)
                .sectionIndex(sectionIndex)
                .sectionSummary(sectionSummary)
                .subject(lecture.getSubject())
                .previousQa(previousQa)
                .build(), types);
    }

    private void requestResources(Long lectureId, Integer sectionIndex, Long summaryId, String sectionSummary,
                                  List<String> types) {
        requireSummary(sectionSummary);
        List<PreviousSummaryPayload> previousSummaries = summaryService
                .findPreviousSummaries(lectureId, sectionIndex, historyProperties.getPreviousSummaryCount())
                .stream()
                .map(prev -> PreviousSummaryPayload.builder()
                        .sectionIndex(prev.getSectionIndex())
                        .summary(prev.getText())
                        .build())
                .toList();
        // 직전 섹션에서 추천한 자료는 다시 추천하지 않도록 제외 목록으로 보냄
        List<Resource> recent = previousSections(sectionIndex, historyProperties.getPreviousResourceSections())
                .map(range -> resourceRepository.findByLectureIdAndSectionIndexBetweenOrderByIdAsc(
                        lectureId, range.start(), range.end()))
                .orElse(List.of());

        log.info("[Card Request] Resources: lectureId={} section={} types={}", lectureId, sectionIndex, types);
        aiServerClient.requestResourceRecommendation(ResourceRecommendPayload.builder()
                .lectureId(lectureId)
                .summaryId(summaryId)
                .sectionIndex(sectionIndex)
                .sectionSummary(sectionSummary)
                .previousSummaries(previousSummaries)
                .ytExclude(excludeKeys(recent, Resource::getTitle, Resource.Type.VIDEO, Resource.Type.YOUTUBE))
                .wikiExclude(excludeKeys(recent, Resource::getTitle, Resource.Type.WIKI))
                .paperExclude(excludeKeys(recent, Resource::getUrl, Resource.Type.PAPER))
                .googleExclude(excludeKeys(recent, Resource::getUrl, Resource.Type.GOOGLE))
                .build(), types);
    }

    // 지정한 종류의 자료에서 AI 서버가 중복 판정에 쓰는 값(제목 또는 URL)을 중복 없이 모음
    private static List<String> excludeKeys(List<Resource> resources, Function<Resource, String> key,
                                            Resource.Type... types) {
        List<Resource.Type> targetTypes = List.of(types);
        return resources.stream()
                .filter(resource -> targetTypes.contains(resource.getType()))
                .map(key)
                .filter(Objects::nonNull)
                .map(String::trim)
                .filter(value -> !value.isEmpty())
                .distinct()
                .toList();
    }

    private record SectionRange(int start, int end) {}

    // 현재 섹션 바로 앞의 window개 섹션. 첫 섹션이거나 window가 0 이하면 없음
    private static Optional<SectionRange> previousSections(Integer sectionIndex, int window) {
        if (sectionIndex == null || sectionIndex <= 0 || window <= 0) {
            return Optional.empty();
        }
        return Optional.of(new SectionRange(Math.max(0, sectionIndex - window), sectionIndex - 1));
    }

    private static void requireSummary(String sectionSummary) {
        if (sectionSummary == null || sectionSummary.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "section summary is required");
        }
    }

    // 최종 요약 콜백이 아직 저장 중일 수 있어 잠시 기다리며 다시 찾음
    private Optional<Summary> findSummaryWithRetry(Long lectureId, Integer sectionIndex) {
        for (int attempt = 1; attempt <= SUMMARY_LOOKUP_ATTEMPTS; attempt++) {
            Optional<Summary> summary = summaryService.findByLectureAndSection(lectureId, sectionIndex);
            if (summary.isPresent()) {
                return summary;
            }
            if (attempt < SUMMARY_LOOKUP_ATTEMPTS) {
                try {
                    Thread.sleep(SUMMARY_LOOKUP_DELAY_MS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        log.warn("[Card Request] Skipped (summary not found): lectureId={} section={}", lectureId, sectionIndex);
        return Optional.empty();
    }
}
