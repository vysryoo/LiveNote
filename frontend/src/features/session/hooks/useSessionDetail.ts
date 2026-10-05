import { queryOptions, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchSessionDetail, findLastSectionIndex, sessionKeys } from "../api/sessionApi";

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

/**
 * 현재 녹음 중인 섹션 번호를 조회한다.
 *
 * 처음에는 저장된 데이터의 마지막 섹션으로 시작하고, 이후에는 `/section` 메시지가 갱신한다.
 * 상세가 다시 조회돼도 섹션 번호가 뒤로 가지 않도록 기존 값과 비교해 큰 값을 쓴다.
 *
 * @param lectureId 강의 ID
 * @returns 현재 섹션 번호. 상세를 받기 전에는 0
 */
export function useCurrentSection(lectureId: number): number {
  const queryClient = useQueryClient();
  const key = sessionKeys.currentSection(lectureId);
  const { data } = useQuery({
    queryKey: key,
    queryFn: async () => {
      const detail = await queryClient.ensureQueryData(sessionDetailQuery(lectureId));
      return Math.max(queryClient.getQueryData<number>(key) ?? 0, findLastSectionIndex(detail));
    },
    staleTime: Infinity,
  });
  return data ?? 0;
}
