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

        List<Resource> saved = dto.getResources().stream()
                .map(item -> Resource.builder()
                        .lectureId(dto.getLectureId())
                        .summaryId(dto.getSummaryId())
                        .sectionIndex(dto.getSectionIndex())
                        .type(Resource.Type.fromString(item.getType()))
                        .title(item.getTitle())
                        .url(item.getUrl())
                        .text(item.getDescription())
                        .score(item.getScore())
                        .reason(item.getReason())
                        .detail(toJsonNode(item.getDetail()))
                        .build())
                .map(resourceRepository::save)
                .toList();

        List<ResourceResponseDto> items = saved.stream()
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
}
