package com.capstone.livenote.card;

import com.capstone.livenote.ai.ResourceCallbackDto;
import com.capstone.livenote.global.stomp.StreamGateway;
import com.fasterxml.jackson.databind.JsonNode;
import com.capstone.livenote.global.redis.RedisLock;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import org.springframework.transaction.TransactionStatus;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ResourceCallbackServiceTest {

    @Mock ResourceRepository resourceRepository;
    @Mock StreamGateway streamGateway;
    @Mock RedisLock redisLock;
    @Mock TransactionTemplate transactionTemplate;

    @BeforeEach
    void runLockAndTransactionInline() {
        doAnswer(inv -> {
            inv.<Runnable>getArgument(1).run();
            return null;
        }).when(redisLock).run(anyString(), any());
        doAnswer(inv -> {
            inv.<Consumer<TransactionStatus>>getArgument(0).accept(null);
            return null;
        }).when(transactionTemplate).executeWithoutResult(any());
    }

    @Test
    void saveResourceWithReasonAndDetail() {
        // given
        List<Resource> stored = new java.util.ArrayList<>();
        when(resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(1L, 3))
                .thenAnswer(inv -> List.copyOf(stored));
        when(resourceRepository.save(any(Resource.class))).thenAnswer(inv -> {
            Resource r = inv.getArgument(0);
            r.setId(99L);
            stored.add(r);
            return r;
        });

        var item = ResourceCallbackDto.ResourceItem.builder()
                .type("video")
                .title("Retry patterns")
                .url("https://example.com")
                .description("desc")
                .score(88.1)
                .reason("because")
                .detail(Map.of("provider", "youtube", "lang", "en"))
                .build();

        var dto = ResourceCallbackDto.builder()
                .lectureId(1L)
                .summaryId(10L)
                .sectionIndex(3)
                .resources(List.of(item))
                .build();

        // when
        var service = new ResourceCallbackService(resourceRepository, streamGateway, new com.fasterxml.jackson.databind.ObjectMapper(),
                redisLock, transactionTemplate);
        service.handleResourceCallback(dto);

        // then
        ArgumentCaptor<Resource> captor = ArgumentCaptor.forClass(Resource.class);
        verify(resourceRepository).save(captor.capture());
        Resource saved = captor.getValue();
        assertThat(saved.getReason()).isEqualTo("because");
        JsonNode node = saved.getDetail();
        assertThat(node.get("provider").asText()).isEqualTo("youtube");
        assertThat(node.get("lang").asText()).isEqualTo("en");

        ArgumentCaptor<List<com.capstone.livenote.card.ResourceResponseDto>> streamCaptor =
                ArgumentCaptor.forClass(List.class);
        verify(streamGateway).sendResources(eq(1L), eq(3), streamCaptor.capture());
        assertThat(streamCaptor.getValue()).hasSize(1);
    }
}
