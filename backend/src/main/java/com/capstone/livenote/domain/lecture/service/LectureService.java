package com.capstone.livenote.domain.lecture.service;

import com.capstone.livenote.domain.bookmark.dto.BookmarkResponseDto;
import com.capstone.livenote.domain.bookmark.entity.Bookmark;
import com.capstone.livenote.domain.bookmark.repository.BookmarkRepository;
import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.dto.LectureResponseDto;
import com.capstone.livenote.domain.lecture.dto.SessionDetailResponse;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.qna.dto.QnaResponseDto;
import com.capstone.livenote.domain.qna.repository.QnaRepository;
import com.capstone.livenote.domain.resource.dto.ResourceResponseDto;
import com.capstone.livenote.domain.resource.repository.ResourceRepository;
import com.capstone.livenote.domain.summary.dto.SummaryResponseDto;
import com.capstone.livenote.domain.summary.repository.SummaryRepository;
import com.capstone.livenote.domain.transcript.dto.TranscriptResponseDto;
import com.capstone.livenote.domain.transcript.repository.TranscriptRepository;
import com.capstone.livenote.domain.user.entity.User;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;
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

    @Transactional
    public Lecture create(Long userId, CreateLectureRequestDto req){
        log.info("💾 [DB WRITE] Creating new lecture: userId={} title={}", userId, req.getTitle());
        //var user = new User();      // userId만 세팅
        //user.setId(userId);

        Lecture lec = Lecture.builder()
                .userId(userId)
                .title(req.getTitle())
                .subject(req.getSubject())
                .sttLanguage(req.getSttLanguage())
                .status(Lecture.Status.RECORDING)
                .build();

        Lecture saved = lectureRepo.save(lec);
        log.info("✅ [DB WRITE] Lecture created: id={} title={}", saved.getId(), saved.getTitle());
        return saved;
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
        log.info("📂 [DB READ] Fetching lecture list: userId={}", userId);
        Page<Lecture> result = lectureRepo.findByUserIdOrderByCreatedAtDesc(userId, pageable);
        log.info("✅ [DB READ] Loaded {} lectures for userId={}", result.getContent().size(), userId);
        return result;
    }
    @Transactional(readOnly = true)
    public Lecture get(Long id){
        log.info("📂 [DB READ] Fetching lecture: lectureId={}", id);
        Lecture lecture = lectureRepo.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
        log.info("✅ [DB READ] Loaded lecture: id={} title={}", lecture.getId(), lecture.getTitle());
        return lecture;
    }

    @Transactional(readOnly = true)
    public LectureResponseDto getWithBookmarks(Long lectureId, Long userId) {
        Lecture lecture = get(lectureId);
        List<BookmarkResponseDto> bookmarks = loadBookmarks(userId, lectureId);
        return LectureResponseDto.from(lecture, bookmarks);
    }
    @Transactional
    public void delete(Long id){
        log.info("🗑️ [DB DELETE] Deleting lecture: lectureId={}", id);
        lectureRepo.deleteById(id);
        log.info("✅ [DB DELETE] Lecture deleted: lectureId={}", id);
    }
//    @Transactional
//    public void startProcessing(Long id){
//        lectureRepo.updateStatus(id, Lecture.Status.RECORDING);
//    }
//    @Transactional
//    public void complete(Long id){
//        lectureRepo.updateStatus(id, Lecture.Status.COMPLETED);
//    }

    @Transactional
    public void startRecording(Long id) {
        log.info("💾 [DB WRITE] Starting recording: lectureId={}", id);
        lectureRepo.updateStatus(id, Lecture.Status.RECORDING);
        log.info("✅ [DB WRITE] Recording started: lectureId={}", id);
    }

    // 강의 종료 (녹음 끝 + 상태 COMPLETED)
    @Transactional
    public Lecture endLecture(Long id) {
        log.info("💾 [DB WRITE] Ending lecture: lectureId={}", id);
        Lecture lecture = lectureRepo.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
        lecture.setStatus(Lecture.Status.COMPLETED);
        lecture.setEndAt(java.time.LocalDateTime.now());
        lectureRepo.save(lecture);
        log.info("✅ [DB WRITE] Lecture ended: id={} status=COMPLETED", id);
        return lecture;
    }

    @Transactional
    public Lecture updateLectureTitle(Long lectureId, String title) {
        Lecture lecture = lectureRepo.findById(lectureId)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
        lecture.setTitle(title);
        return lectureRepo.save(lecture);
    }

    // 강의 상세 정보 조회 (transcripts, summaries, resources, qna, bookmarks 포함)
    @Transactional(readOnly = true)
    public SessionDetailResponse getSessionDetail(Long lectureId) {
        log.info("📂 [DB READ] Fetching session detail: lectureId={}", lectureId);
        
        Lecture lecture = lectureRepo.findById(lectureId)
                .orElseThrow(() -> new EntityNotFoundException("lecture"));
        
        var transcripts = transcriptRepository.findByLectureIdOrderByStartSecAsc(lectureId)
                .stream()
                .map(TranscriptResponseDto::from)
                .collect(Collectors.toList());
        
        var summaries = summaryRepository.findByLectureIdOrderBySectionIndexAsc(lectureId)
                .stream()
                .map(SummaryResponseDto::from)
                .collect(Collectors.toList());
        
        // Resource는 lectureId로 조회 후 sectionIndex로 정렬
        var resources = resourceRepository.findByLectureId(lectureId, Pageable.unpaged())
                .stream()
                .sorted((r1, r2) -> Integer.compare(r1.getSectionIndex(), r2.getSectionIndex()))
                .map(ResourceResponseDto::from)
                .collect(Collectors.toList());
        
        var qnas = qnaRepository.findByLectureIdOrderBySectionIndexAsc(lectureId)
                .stream()
                .map(QnaResponseDto::from)
                .collect(Collectors.toList());

        var bookmarks = bookmarkRepository.findByUserIdAndLectureId(lecture.getUserId(), lectureId, Pageable.unpaged())
                .stream()
                .sorted((b1, b2) -> Integer.compare(b1.getSectionIndex(), b2.getSectionIndex()))
                .map(bm -> {
                    Object content = null;

                    // 타겟 타입에 따라 원본 데이터 조회
                    if (bm.getTargetType() == Bookmark.TargetType.QNA) {
                        content = qnaRepository.findById(bm.getTargetId())
                                .map(QnaResponseDto::from)
                                .orElse(null);
                    } else if (bm.getTargetType() == Bookmark.TargetType.RESOURCE) {
                        content = resourceRepository.findById(bm.getTargetId())
                                .map(ResourceResponseDto::from)
                                .orElse(null);
                    }

                    // BookmarkResponseDto 생성 시 content 함께 전달
                    return BookmarkResponseDto.from(bm, content);
                })
                .collect(Collectors.toList());

        log.info("✅ [DB READ] Session detail loaded: lectureId={} transcripts={} summaries={} resources={} qnas={} bookmarks={}",
                lectureId, transcripts.size(), summaries.size(), resources.size(), qnas.size(), bookmarks.size());

        return SessionDetailResponse.from(lecture, transcripts, summaries, resources, qnas, bookmarks);
    }


    @Transactional
    public void updateCollectionId(Long lectureId, String collectionId) {
        Lecture lecture = get(lectureId); // 기존 get 메서드 활용
        lecture.setCollectionId(collectionId);
        // 더티 체킹으로 자동 저장
    }

    private List<BookmarkResponseDto> loadBookmarks(Long userId, Long lectureId) {
        return bookmarkRepository.findByUserIdAndLectureId(userId, lectureId)
                .stream()
                .sorted((b1, b2) -> Integer.compare(b1.getSectionIndex(), b2.getSectionIndex()))
                .map(bm -> {
                    Object content = null;

                    if (bm.getTargetType() == Bookmark.TargetType.QNA) {
                        content = qnaRepository.findById(bm.getTargetId())
                                .map(QnaResponseDto::from)
                                .orElse(null);
                    } else if (bm.getTargetType() == Bookmark.TargetType.RESOURCE) {
                        content = resourceRepository.findById(bm.getTargetId())
                                .map(ResourceResponseDto::from)
                                .orElse(null);
                    }

                    return BookmarkResponseDto.from(bm, content);
                })
                .collect(Collectors.toList());
    }
}
