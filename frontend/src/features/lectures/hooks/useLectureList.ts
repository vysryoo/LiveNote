import { useInfiniteQuery } from "@tanstack/react-query";
import { fetchLecturePage, lectureKeys } from "../api/lecturesApi";

/**
 * 로그인한 사용자의 강의 목록을 페이지 단위로 조회한다.
 *
 * 처음에는 첫 페이지만 받고, `fetchNextPage`로 다음 페이지를 이어 받는다.
 *
 * @returns Infinite Query 결과
 */
export function useLectureList() {
  return useInfiniteQuery({
    queryKey: lectureKeys.list,
    queryFn: ({ pageParam }) => fetchLecturePage(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage, pages) => (lastPage.hasNext ? pages.length : undefined),
  });
}
