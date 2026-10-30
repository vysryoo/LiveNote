package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.ResourceCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.capstone.livenote.global.redis.RedisLock;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;
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
        String lockKey = "livenote:lock:lecture:" + dto.getLectureId() + ":section:" + dto.getSectionIndex() + ":resource";
        redisLock.run(lockKey, () -> transactionTemplate.executeWithoutResult(status -> saveCards(dto)));
    }

    private void saveCards(ResourceCallbackDto dto) {
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
        existing.forEach(r -> signature.add(CardIds.signature(r.getTitle(), r.getUrl())));

        int cursor = CardIds.nextIndex(existing.stream().map(Resource::getCardId).toList());

        for (var item : dto.getResources()) {
            String sig = CardIds.signature(item.getTitle(), item.getUrl());
            if (signature.contains(sig)) {
                log.debug("Skipping duplicate resource for lecture {} section {}: {}", dto.getLectureId(), dto.getSectionIndex(), item.getTitle());
                continue;
            }
            String cardId = CardIds.build("resource", dto.getLectureId(), dto.getSectionIndex(), cursor++);
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

            // 완성된 카드를 즉시 전송. 글자가 써지는 연출은 프론트엔드가 담당
            streamGateway.sendStreamComplete(dto.getLectureId(), "resource_stream", cardId, ResourceResponseDto.from(saved));
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
}
