package com.capstone.livenote.domain.resource.service;

import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import org.springframework.transaction.annotation.Transactional;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;


@Service
@RequiredArgsConstructor
public class ResourceService {
    private final ResourceRepository repo;
    @Transactional(readOnly = true)
    public List<Resource> bySummary(Long summaryId, String type){
        var list = repo.findBySummaryIdOrderByScoreDesc(summaryId);
        if (type == null) return list;

        return list.stream()
                .filter(r -> r.getType().name().equalsIgnoreCase(type))
                .toList();
    }
}



