package com.capstone.livenote.lecture;

import com.capstone.livenote.ai.AiServerClient;
import com.capstone.livenote.card.QnaResponseDto;
import com.capstone.livenote.card.QnaRepository;
import com.capstone.livenote.card.ResourceResponseDto;
import com.capstone.livenote.card.ResourceRepository;
import com.capstone.livenote.summary.SummaryResponseDto;
import com.capstone.livenote.summary.SummaryRepository;
import com.capstone.livenote.recording.TranscriptResponseDto;
import com.capstone.livenote.recording.TranscriptRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class LectureService {
    private final LectureRepository lectureRepo;
    private final TranscriptRepository transcriptRepository;
    private final SummaryRepository summaryRepository;
    private final ResourceRepository resourceRepository;
    private final QnaRepository qnaRepository;
    private final BookmarkRepository bookmarkRepository;
    private final AiServerClient aiServerClient;

    @Transactional
    public Lecture create(Long userId, CreateLectureRequestDto req){
        Lecture lec = Lecture.builder()
                .userId(userId)
                .title(req.title())
                .subject(req.subject())
                .sttLanguage(req.sttLanguage())
                .status(Lecture.Status.RECORDING)
                .build();

        Lecture saved = lectureRepo.save(lec);
        log.info("Lecture created: id={} userId={}", saved.getId(), userId);
        return saved;
    }

    /**
     * 강의를 만들고 강의 자료 PDF를 AI 서버의 검색 저장소에 올린다.
     *
     * 강의 저장과 PDF 업로드는 한 트랜잭션으로 묶지 않는다. 업로드가 실패해도 이미 저장한 강의는 남는다.
     *
     * @param userId 강의를 만드는 사용자 ID
     * @param req 강의 정보
     * @param pdf 강의 자료 PDF
     * @return 만든 강의. 업로드한 자료의 컬렉션 ID가 저장됨
     * @throws RuntimeException AI 서버 업로드에 실패한 경우
     */
    public Lecture createWithPdf(Long userId, CreateLectureRequestDto req, MultipartFile pdf) {
        Lecture lecture = create(userId, req);
        lecture.setCollectionId(aiServerClient.upsertPdf(lecture.getId(), pdf));
        return lectureRepo.save(lecture);
    }

    /**
     * 요청한 사용자 본인의 강의를 조회한다.
     *
     * @param lectureId 강의 ID
     * @param userId 요청한 사용자 ID
     * @return 강의
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우.
     *         강의 존재 여부가 드러나지 않도록 두 경우를 구분하지 않음
     */
    @Transactional(readOnly = true)
    public Lecture getOwned(Long lectureId, Long userId) {
        return lectureRepo.findByIdAndUserId(lectureId, userId)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
    }

    @Transactional(readOnly = true)
    public Page<Lecture> list(Long userId, Pageable pageable){
        return lectureRepo.findByUserIdOrderByCreatedAtDesc(userId, pageable);
    }
    @Transactional(readOnly = true)
    public Lecture get(Long id){
        return lectureRepo.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
    }

    /**
     * 요청한 사용자 본인의 강의를 삭제한다.
     *
     * @param lectureId 강의 ID
     * @param userId 요청한 사용자 ID
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우
     */
    @Transactional
    public void delete(Long lectureId, Long userId){
        lectureRepo.delete(getOwned(lectureId, userId));
        log.info("Lecture deleted: id={}", lectureId);
    }

    /**
     * 강의를 종료 상태로 바꾸고, 제목이 주어지면 함께 저장한다.
     *
     * @param id 강의 ID
     * @param userId 요청한 사용자 ID
     * @param title 저장할 제목. null이거나 공백뿐이면 기존 제목 유지
     * @return 종료된 강의
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우
     */
    @Transactional
    public Lecture endLecture(Long id, Long userId, String title) {
        Lecture lecture = getOwned(id, userId);
        if (title != null && !title.isBlank()) {
            lecture.setTitle(title.trim());
        }
        lecture.setStatus(Lecture.Status.COMPLETED);
        lecture.setEndAt(LocalDateTime.now());
        lectureRepo.save(lecture);
        log.info("Lecture ended: id={}", id);
        return lecture;
    }

    /**
     * 요청한 사용자 본인의 강의 제목을 바꾼다.
     *
     * @param lectureId 강의 ID
     * @param userId 요청한 사용자 ID
     * @param title 새 제목
     * @return 제목을 바꾼 강의
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우
     */
    @Transactional
    public Lecture updateLectureTitle(Long lectureId, Long userId, String title) {
        Lecture lecture = getOwned(lectureId, userId);
        lecture.setTitle(title);
        return lectureRepo.save(lecture);
    }

    /**
     * 요청한 사용자 본인 강의의 전사, 요약, 자료, QnA, 북마크를 한 번에 조회한다.
     *
     * @param lectureId 강의 ID
     * @param userId 요청한 사용자 ID
     * @return 강의 상세
     * @throws EntityNotFoundException 강의가 없거나 다른 사용자의 강의인 경우
     */
    @Transactional(readOnly = true)
    public SessionDetailResponse getSessionDetail(Long lectureId, Long userId) {
        Lecture lecture = getOwned(lectureId, userId);
        
        var transcripts = transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId)
                .stream()
                .map(TranscriptResponseDto::from)
                .collect(Collectors.toList());
        
        var summaries = summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId)
                .stream()
                .map(SummaryResponseDto::from)
                .collect(Collectors.toList());
        
        var resources = resourceRepository.findByLectureIdOrderBySectionIndexAscIdAsc(lectureId)
                .stream()
                .map(ResourceResponseDto::from)
                .collect(Collectors.toList());
        
        var qnas = qnaRepository.findByLectureIdOrderBySectionIndexAscIdAsc(lectureId)
                .stream()
                .map(QnaResponseDto::from)
                .collect(Collectors.toList());

        var bookmarks = bookmarkRepository.findByUserIdAndLectureIdOrderBySectionIndexAscIdAsc(userId, lectureId)
                .stream()
                .map(BookmarkResponseDto::from)
                .collect(Collectors.toList());


        return SessionDetailResponse.from(lecture, transcripts, summaries, resources, qnas, bookmarks);
    }

}
