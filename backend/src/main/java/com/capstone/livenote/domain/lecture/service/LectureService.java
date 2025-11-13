package com.capstone.livenote.domain.lecture.service;

import com.capstone.livenote.domain.lecture.dto.CreateLectureRequestDto;
import com.capstone.livenote.domain.lecture.entity.Lecture;
import com.capstone.livenote.domain.lecture.repository.LectureRepository;
import com.capstone.livenote.domain.user.entity.User;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.transaction.annotation.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class LectureService {
    private final LectureRepository lectureRepo;

    @Transactional
    public Lecture create(Long userId, CreateLectureRequestDto req){
        var user = new User();      // userId만 세팅
        user.setId(userId);

        Lecture lec = Lecture.builder()
                .userId(userId)
                .title(req.getTitle())
                .subject(req.getSubject())
                .sttLanguage(req.getSttLanguage())
                .status(Lecture.Status.RECORDING)
                .build();

        return lectureRepo.save(lec);
    }

    @Transactional(readOnly = true)
    public Page<Lecture> list(Long userId, Pageable pageable){
        return lectureRepo.findByUserIdOrderByCreatedAtDesc(userId, pageable);
    }
    @Transactional(readOnly = true)
    public Lecture get(Long id){
        return lectureRepo.findById(id).orElseThrow(() -> new EntityNotFoundException("lecture"));
    }
    @Transactional
    public void delete(Long id){ lectureRepo.deleteById(id); }
    @Transactional
    public void startProcessing(Long id){ lectureRepo.updateStatus(id, Lecture.Status.RECORDING); }
    @Transactional
    public void complete(Long id){ lectureRepo.updateStatus(id, Lecture.Status.COMPLETED); }
}