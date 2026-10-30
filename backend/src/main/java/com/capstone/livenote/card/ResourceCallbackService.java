package com.capstone.livenote.card;

import com.capstone.livenote.ai.ResourceCallbackDto;
import com.capstone.livenote.global.stomp.StreamGateway;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.capstone.livenote.global.redis.RedisKeys;
import com.capstone.livenote.global.redis.RedisLock;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
import lombok.extern.slf4j.Slf4j;

import java.util.List;
import java.util.HashSet;
import java.util.Set;

/**
 * AI 서버의 자료 추천 콜백을 받아 자료 카드를 저장하고 실시간으로 보낸다.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ResourceCallbackService {

    private final ResourceRepository resourceRepository;
    private final StreamGateway streamGateway;
    private final ObjectMapper objectMapper;
    private final RedisLock redisLock;
    private final TransactionTemplate transactionTemplate;

    /**
     * AI 서버가 보낸 카드를 저장하고 실시간으로 전송한다.
     *
     * 같은 섹션의 콜백은 서버 여러 대에 걸쳐 하나씩 처리한다. 카드 번호를 기존 카드의 최댓값 다음으로 정하므로
     * 동시에 처리하면 번호가 겹친다. 잠금은 DB 저장이 확정된 뒤에 푼다.
     *
     * @param dto AI 서버 콜백 본문
     * @throws IllegalStateException 잠금을 얻지 못한 경우
     */
    public void handleResourceCallback(ResourceCallbackDto dto) {
        redisLock.run(RedisKeys.resourceLock(dto.lectureId(), dto.sectionIndex()), () -> transactionTemplate.executeWithoutResult(status -> saveCards(dto)));
    }

    private void saveCards(ResourceCallbackDto dto) {
        log.info("Resource callback: lectureId={} section={} summaryId={} size={}",
                dto.lectureId(), dto.sectionIndex(), dto.summaryId(),
                dto.resources() == null ? 0 : dto.resources().size());

        if (dto.resources() == null || dto.resources().isEmpty()) {
            log.info("Resource callback skipped: empty payload");
            return;
        }

        List<Resource> existing = resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                dto.lectureId(), dto.sectionIndex()
        );

        Set<String> signature = new HashSet<>();
        existing.forEach(r -> signature.add(CardIds.signature(r.getTitle(), r.getUrl())));

        int cursor = CardIds.nextIndex(existing.stream().map(Resource::getCardId).toList());

        for (var item : dto.resources()) {
            String sig = CardIds.signature(item.title(), item.url());
            if (signature.contains(sig)) {
                log.debug("Skipping duplicate resource for lecture {} section {}: {}", dto.lectureId(), dto.sectionIndex(), item.title());
                continue;
            }
            String cardId = CardIds.build("resource", dto.lectureId(), dto.sectionIndex(), cursor++);
            if (resourceRepository.existsByLectureIdAndSectionIndexAndCardId(dto.lectureId(), dto.sectionIndex(), cardId)) {
                continue;
            }

            Resource saved = resourceRepository.save(
                    Resource.builder()
                            .lectureId(dto.lectureId())
                            .summaryId((dto.summaryId() == null || dto.summaryId() == 0L) ? null : dto.summaryId())
                            .sectionIndex(dto.sectionIndex())
                            .cardId(cardId)
                            .type(Resource.Type.fromString(item.type()))
                            .title(item.title())
                            .url(item.url())
                            .text(item.description())
                            .score(item.score())
                            .reason(item.reason())
                            .detail(toJsonNode(item.detail()))
                            .build()
            );
            signature.add(sig);

            // 완성된 카드를 즉시 전송. 글자가 써지는 연출은 프론트엔드가 담당
            streamGateway.sendStreamComplete(dto.lectureId(), "resource_stream", cardId, ResourceResponseDto.from(saved));
        }

        List<Resource> allResources = resourceRepository.findByLectureIdAndSectionIndexOrderByIdAsc(
                dto.lectureId(), dto.sectionIndex()
        );

        List<ResourceResponseDto> items = allResources.stream()
                .map(ResourceResponseDto::from)
                .toList();

        streamGateway.sendResources(dto.lectureId(), dto.sectionIndex(), items);
    }

    private JsonNode toJsonNode(Object value) {
        if (value == null) {
            return null;
        }
        return objectMapper.valueToTree(value);
    }
}
