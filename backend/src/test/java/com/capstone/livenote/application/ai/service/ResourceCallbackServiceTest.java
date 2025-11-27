package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ResourceCallbackServiceTest {

    @Mock ResourceRepository resourceRepository;
    @Mock StreamGateway streamGateway;

    @Test
    void saveResourceWithReasonAndDetail() {
        // given
        when(resourceRepository.save(any(Resource.class))).thenAnswer(inv -> {
            Resource r = inv.getArgument(0);
            r.setId(99L);
            return r;
        });

        var item = new ResourceCallbackDto.ResourceItem();
        item.setType("video");
        item.setTitle("Retry patterns");
        item.setUrl("https://example.com");
        item.setDescription("desc");
        item.setScore(88.1);
        item.setReason("because");
        item.setDetail(Map.of("provider", "youtube", "lang", "en"));

        var dto = new ResourceCallbackDto();
        dto.setLectureId(1L);
        dto.setSummaryId(10L);
        dto.setSectionIndex(3);
        dto.setResources(List.of(item));

        // when
        var service = new ResourceCallbackService(resourceRepository, streamGateway, new com.fasterxml.jackson.databind.ObjectMapper());
        service.handleResourceCallback(dto);

        // then
        ArgumentCaptor<Resource> captor = ArgumentCaptor.forClass(Resource.class);
        verify(resourceRepository).save(captor.capture());
        Resource saved = captor.getValue();
        assertThat(saved.getReason()).isEqualTo("because");
        JsonNode node = saved.getDetail();
        assertThat(node.get("provider").asText()).isEqualTo("youtube");
        assertThat(node.get("lang").asText()).isEqualTo("en");

        ArgumentCaptor<List<com.capstone.livenote.domain.resource.dto.ResourceResponseDto>> streamCaptor =
                ArgumentCaptor.forClass(List.class);
        verify(streamGateway).sendResources(eq(1L), eq(3), streamCaptor.capture());
        assertThat(streamCaptor.getValue()).hasSize(1);
    }
}
