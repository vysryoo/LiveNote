package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
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
    public void saveResources(ResourceCallbackDto dto) {

        // 1) 엔티티 저장
        List<Resource> toSave = new ArrayList<>();

        for (ResourceCallbackDto.ResourceItem item : dto.getResources()) {

            Resource.Type type = Resource.Type.valueOf(
                    item.getType().toUpperCase()   // "blog" → "BLOG"
            );

            Resource resource = Resource.builder()
                    .lectureId(dto.getLectureId())
                    .summaryId(dto.getSummaryId())
                    .userId(null)                          // 필요하면 DTO에 추가
                    .sectionIndex(dto.getSectionIndex())
                    .type(type)
                    .title(item.getTitle())
                    .text(item.getDescription())
                    .url(item.getUrl())
                    .thumbnail(null)                       // 필요하면 DTO에 추가
                    .score(item.getScore())
                    .build();

            toSave.add(resource);
        }

        List<Resource> saved = resourceRepository.saveAll(toSave);

        // 2) 프론트에 보낼 payload 만들기
        List<Map<String, Object>> payload = new ArrayList<>();
        for (Resource r : saved) {
            Map<String, Object> map = new HashMap<>();
            map.put("id", r.getId());
            map.put("lectureId", r.getLectureId());
            map.put("summaryId", r.getSummaryId());
            map.put("userId", r.getUserId());
            map.put("sectionIndex", r.getSectionIndex());
            map.put("type", r.getType().name());
            map.put("title", r.getTitle());
            map.put("text", r.getText());
            map.put("url", r.getUrl());
            map.put("thumbnail", r.getThumbnail());
            map.put("score", r.getScore());
            payload.add(map);
        }

        // 3) WebSocket(STOMP) 전송
        streamGateway.sendResource(dto.getLectureId(), payload);
    }
}
