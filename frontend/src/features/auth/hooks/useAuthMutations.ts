import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { setAuthToken } from "@/shared/lib/authToken";
import type { LanguageCode } from "@/shared/i18n";
import { authKeys, login, signup, updatePassword, updateUiLanguage } from "../api/authApi";
import type { AuthResponse } from "../api/schemas";

function startSession(queryClient: QueryClient, { token, user }: AuthResponse) {
  setAuthToken(token);
  queryClient.setQueryData(authKeys.me, user);
}

/**
 * 로그인 mutation을 반환한다. 성공 시 토큰을 저장하고 사용자 정보 캐시를 채운다.
 *
 * @returns TanStack Query mutation
 */
export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: login,
    onSuccess: (response) => startSession(queryClient, response),
  });
}

/**
 * 회원가입 mutation을 반환한다. 가입 응답의 토큰으로 바로 로그인 상태가 된다.
 *
 * @returns TanStack Query mutation
 */
export function useSignup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: signup,
    onSuccess: (response) => startSession(queryClient, response),
  });
}

/**
 * 설정 저장 mutation을 반환한다. 성공 시 사용자 정보 캐시를 갱신한다.
 *
 * @returns TanStack Query mutation
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (settings: {
      language: LanguageCode;
      password?: { currentPassword: string; newPassword: string };
    }) => {
      // 사용자가 틀릴 수 있는 비밀번호 변경을 먼저 처리해 실패 시 언어도 바뀌지 않게 함
      if (settings.password) await updatePassword(settings.password);
      return updateUiLanguage(settings.language);
    },
    onSuccess: (user) => queryClient.setQueryData(authKeys.me, user),
  });
}
