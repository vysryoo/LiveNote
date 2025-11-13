package com.capstone.livenote.application.ai.service;

import com.capstone.livenote.application.ai.dto.AiCallbackDto;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.qna.entity.Qna;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.entity.Resource;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.summary.entity.Summary;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.transcript.entity.Transcript;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import com.capstone.livenote.domain.lecture.entity.Lecture;


@Service
@RequiredArgsConstructor
public class AiCallbackService {
    private final TranscriptRepository trRepo;
    private final SummaryRepository smRepo;
    private final ResourceRepository rsRepo;
    private final QnaRepository qnaRepo;
    private final LectureRepository lectureRepo;

    @Transactional
    public void apply(AiCallbackDto payload){
        Long lectureId = payload.getLectureId();

        // (선택) 전사 콜백 저장
        if (payload.getTranscripts() != null) {
            for (var t : payload.getTranscripts()) {
                int sectionIndex = Math.floorDiv(t.getStartSec(), 30);
                trRepo.save(Transcript.builder()
                        .lectureId(lectureId)      // FK(Long)
                        .sectionIndex(sectionIndex)
                        .startSec(t.getStartSec())
                        .endSec(t.getEndSec())
                        .text(t.getText())
                        .build());
            }
        }

        // 리소스 저장
        if (payload.getResources() != null) {
            for (var r : payload.getResources()) {
                // 우리가 요약을 저장하므로 summaryId를 찾고 싶다면 조회 (없으면 null)
                Long summaryId = smRepo.findByLectureIdAndSectionIndex(lectureId, r.getSectionIndex())
                        .map(Summary::getId)
                        .orElse(null);

                rsRepo.save(Resource.builder()
                        .lectureId(lectureId)           // FK(Long)
                        .summaryId(summaryId)           // FK(Long, nullable)
                        .userId(null)                   // 필요 시 설정
                        .sectionIndex(r.getSectionIndex())
                        .type(Resource.Type.valueOf(r.getType().toUpperCase()))
                        .title(r.getTitle())
                        .text(r.getText())
                        .url(r.getUrl())
                        .thumbnail(r.getThumbnail())
                        .score(r.getScore())
                        .build());
            }
        }

        // QnA 저장
        if (payload.getQna() != null) {
            for (var q : payload.getQna()) {
                qnaRepo.save(Qna.builder()
                        .lectureId(lectureId)           // FK(Long)
                        .sectionIndex(q.getSectionIndex())
                        .type(Qna.Type.valueOf(q.getType().toUpperCase()))
                        .question(q.getQuestion())
                        .answer(q.getAnswer())
                        .build());
            }
        }

        // 완료 상태 반영 (부분 콜백이 아니면 DONE)
        if (!payload.isPartial()) {
            lectureRepo.updateStatus(lectureId, Lecture.Status.COMPLETED);
        }
    }
}
