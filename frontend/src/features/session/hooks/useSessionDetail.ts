import { queryOptions, useQuery } from "@tanstack/react-query";
import { fetchSessionDetail, sessionKeys } from "../api/sessionApi";

/**
 * 강의 상세 조회 설정을 만든다. 훅과 다른 Query 호출이 같은 키와 조회 함수를 공유하기 위함.
 *
 * @param lectureId 강의 ID
 * @returns TanStack Query 조회 설정
 */
export function sessionDetailQuery(lectureId: number) {
  return queryOptions({
    queryKey: sessionKeys.detail(lectureId),
    queryFn: () => fetchSessionDetail(lectureId),
    // 실시간 메시지가 캐시를 직접 갱신하므로 창 포커스 때마다 다시 받지 않음
    staleTime: Infinity,
  });
}

/**
 * 강의 상세(전사, 요약, QnA, 자료, 북마크 포함)를 조회한다.
 *
 * @param lectureId 강의 ID
 * @returns Query 결과
 */
export function useSessionDetail(lectureId: number) {
  return useQuery(sessionDetailQuery(lectureId));
}
