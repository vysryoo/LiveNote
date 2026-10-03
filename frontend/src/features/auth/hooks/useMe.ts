import { useQuery } from "@tanstack/react-query";
import { authKeys, fetchMe } from "../api/authApi";

/**
 * 로그인한 사용자 정보를 조회한다.
 *
 * @returns Query 결과. `data`가 `null`이면 비로그인 상태
 */
export function useMe() {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: fetchMe,
    // 사용자 정보는 이 앱의 로그인·설정 변경으로만 바뀌고 그때 캐시를 직접 갱신하므로 재조회 불필요
    staleTime: Infinity,
    // 실패를 비로그인으로 취급하므로 재시도로 화면 진입을 늦추지 않음
    retry: false,
  });
}
