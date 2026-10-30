package com.capstone.livenote.lecture;

/**
 * 강의 종료 요청.
 *
 * @param title 종료하면서 저장할 강의 제목. 비어 있으면 제목을 바꾸지 않음
 */
public record EndLectureRequest(String title) {
}
