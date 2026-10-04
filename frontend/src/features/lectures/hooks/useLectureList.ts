import { useQuery } from "@tanstack/react-query";
import { fetchLectures, lectureKeys } from "../api/lecturesApi";

/**
 * 로그인한 사용자의 강의 목록을 조회한다.
 *
 * @returns Query 결과
 */
export function useLectureList() {
  return useQuery({ queryKey: lectureKeys.list, queryFn: fetchLectures });
}
