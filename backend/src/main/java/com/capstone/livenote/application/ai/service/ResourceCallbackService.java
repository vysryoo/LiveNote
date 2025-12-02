package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.HashSet;
import java.util.Set;


@Service
@RequiredArgsConstructor
@Slf4j
public class ResourceCallbackService {

    private final ResourceRepository resourceRepository;
    private final StreamGateway streamGateway;
    private final ObjectMapper objectMapper;

    @Transactional
    public void handleResourceCallback(ResourceCallbackDto dto) {

        log.info("Resource callback: lectureId={} section={} summaryId={} size={}",
                dto.getLectureId(), dto.getSectionIndex(), dto.getSummaryId(),
                dto.getResources() == null ? 0 : dto.getResources().size());

        if (dto.getResources() == null || dto.getResources().isEmpty()) {
            log.info("Resource callback skipped: empty payload");
            return;
        }

        List<Resource> existing = resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                dto.getLectureId(), dto.getSectionIndex()
        );

        Set<String> signature = new HashSet<>();
        existing.forEach(r -> signature.add(sig(r.getTitle(), r.getUrl())));

        int cursor = CardIdHelper.CARD_INDEX_OFFSET + existing.size();

        for (var item : dto.getResources()) {
            String sig = sig(item.getTitle(), item.getUrl());
            if (signature.contains(sig)) {
                log.debug("Skipping duplicate resource for lecture {} section {}: {}", dto.getLectureId(), dto.getSectionIndex(), item.getTitle());
                continue;
            }
            String cardId = CardIdHelper.buildCardId("resource", dto.getLectureId(), dto.getSectionIndex(), cursor++);
            if (resourceRepository.existsByLectureIdAndSectionIndexAndCardId(dto.getLectureId(), dto.getSectionIndex(), cardId)) {
                continue;
            }

            Resource saved = resourceRepository.save(
                    Resource.builder()
                            .lectureId(dto.getLectureId())
                            .summaryId((dto.getSummaryId() == null || dto.getSummaryId() == 0L) ? null : dto.getSummaryId())
                            .sectionIndex(dto.getSectionIndex())
                            .cardId(cardId)
                            .type(Resource.Type.fromString(item.getType()))
                            .title(item.getTitle())
                            .url(item.getUrl())
                            .text(item.getDescription())
                            .score(item.getScore())
                            .reason(item.getReason())
                            .detail(toJsonNode(item.getDetail()))
                            .build()
            );
            signature.add(sig);

            // 1) 토큰(프리뷰) 스트리밍
            streamGateway.sendStreamToken(
                    dto.getLectureId(),
                    "resource_stream",
                    cardId,
                    preview(item.getDescription(), item.getTitle()),
                    false,
                    null,
                    item.getTitle(),
                    item.getType()
            );
            // 2) 완료 스트리밍 (최종 데이터)
            streamGateway.sendStreamToken(
                    dto.getLectureId(),
                    "resource_stream",
                    cardId,
                    null,
                    true,
                    ResourceResponseDto.from(saved),
                    null,
                    null
            );
        }

        // 2. 전체 조회
        List<Resource> allResources = resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                dto.getLectureId(), dto.getSectionIndex()
        );

        // 3. DTO 변환 및 전송
        List<ResourceResponseDto> items = allResources.stream()
                .map(ResourceResponseDto::from)
                .toList();

        streamGateway.sendResources(dto.getLectureId(), dto.getSectionIndex(), items);
    }

    private JsonNode toJsonNode(Object value) {
        if (value == null) {
            return null;
        }
        return objectMapper.valueToTree(value);
    }

    private String preview(String description, String title) {
        String source = (description != null && !description.isBlank()) ? description : title;
        if (source == null || source.isBlank()) {
            return "";
        }
        String trimmed = source.trim();
        return trimmed.length() <= 30 ? trimmed : trimmed.substring(0, 30);
    }

    private String sig(String title, String url) {
        return (title == null ? "" : title.trim()) + "|" + (url == null ? "" : url.trim());
    }
}
