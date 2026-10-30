package com.capstone.livenote.lecture;

import java.util.List;

/**
 * 강의 목록의 한 페이지.
 *
 * @param items 이 페이지의 강의. 최신순
 * @param total 사용자의 전체 강의 수
 * @param hasNext 다음 페이지가 있는지 여부
 */
public record LecturePageDto(List<LectureResponseDto> items, long total, boolean hasNext) {
}
