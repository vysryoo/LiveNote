package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.QnaCallbackDto;
import com.capstone.livenote.application.ws.StreamGateway;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.global.redis.RedisLock;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InOrder;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import org.springframework.transaction.TransactionStatus;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.List;
import java.util.function.Consumer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class QnaCallbackServiceTest {

    @Mock QnaRepository qnaRepository;
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

    @InjectMocks
    QnaCallbackService service;

    @Test
    void saveQnaWithTypeMapping() {
        List<Qna> stored = new java.util.ArrayList<>();
        when(qnaRepository.findByLectureIdAndSectionIndexOrderByIdAsc(1L, 5))
                .thenAnswer(inv -> List.copyOf(stored));
        when(qnaRepository.save(any(Qna.class))).thenAnswer(inv -> {
            Qna q = inv.getArgument(0);
            q.setId(123L);
            stored.add(q);
            return q;
        });

        var item = new QnaCallbackDto.QnaItem();
        item.setType("application");
        item.setQuestion("재시도 패턴?");
        item.setAnswer("exponential backoff");

        var dto = new QnaCallbackDto();
        dto.setLectureId(1L);
        dto.setSummaryId(10L);
        dto.setSectionIndex(5);
        dto.setQnaList(List.of(item));

        service.handleQnaCallback(dto);

        ArgumentCaptor<Qna> captor = ArgumentCaptor.forClass(Qna.class);
        verify(qnaRepository).save(captor.capture());
        Qna saved = captor.getValue();
        assertThat(saved.getType()).isEqualTo(Qna.Type.APPLICATION);
        assertThat(saved.getSummaryId()).isEqualTo(10L);

        ArgumentCaptor<List<com.capstone.livenote.domain.qna.dto.QnaResponseDto>> streamCaptor =
                ArgumentCaptor.forClass(List.class);
        verify(streamGateway).sendQna(eq(1L), eq(5), streamCaptor.capture());
        assertThat(streamCaptor.getValue()).hasSize(1);
    }

    @Test
    void savesInsideSectionLockAndTransaction() {
        var dto = new QnaCallbackDto();
        dto.setLectureId(1L);
        dto.setSectionIndex(5);
        dto.setQnaList(List.of());

        service.handleQnaCallback(dto);

        InOrder order = inOrder(redisLock, transactionTemplate);
        order.verify(redisLock).run(eq("livenote:lock:lecture:1:section:5:qna"), any());
        order.verify(transactionTemplate).executeWithoutResult(any());
    }
}
