package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;


@Service
@RequiredArgsConstructor
public class ResourceCallbackService {

    private final ResourceRepository resourceRepository;
    private final StreamGateway streamGateway;

    @Transactional
    public void handleResourceCallback(ResourceCallbackDto dto) {

        List<Resource> saved = dto.getResources().stream()
                .map(item -> Resource.builder()
                        .lectureId(dto.getLectureId())
                        .summaryId(dto.getSummaryId())
                        .sectionIndex(dto.getSectionIndex())
                        .type(Resource.Type.valueOf(item.getType().toUpperCase()))
                        .title(item.getTitle())
                        .url(item.getUrl())
                        .text(item.getDescription())
                        .score(item.getScore())
                        .build())
                .map(resourceRepository::save)
                .toList();

        List<ResourceResponseDto> items = saved.stream()
                .map(ResourceResponseDto::from)
                .toList();

        streamGateway.sendResources(dto.getLectureId(), dto.getSectionIndex(), items);
    }
}

