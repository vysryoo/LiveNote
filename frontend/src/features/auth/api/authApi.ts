import { getAuthToken } from "@/shared/lib/authToken";
import { HttpError, request } from "@/shared/lib/http";
import type { LanguageCode } from "@/shared/i18n";
import { authResponseSchema, userSchema, type AuthResponse, type User } from "./schemas";

export const authKeys = {
  me: ["auth", "me"] as const,
};

/**
 * 아이디와 비밀번호로 로그인한다.
 *
 * @param credentials 로그인 아이디와 비밀번호
 * @returns 발급된 토큰과 사용자 정보
 * @throws HttpError 아이디가 없거나(404) 비밀번호가 틀린 경우(400)
 */
export async function login(credentials: {
  loginId: string;
  password: string;
}): Promise<AuthResponse> {
  const body = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
  return authResponseSchema.parse(body);
}

/**
 * 회원가입한다. 백엔드가 가입과 동시에 토큰을 발급한다.
 *
 * @param account 가입 정보
 * @returns 발급된 토큰과 사용자 정보
 * @throws HttpError 아이디 또는 이메일이 중복된 경우(400)
 */
export async function signup(account: {
  loginId: string;
  password: string;
  email: string;
  name: string;
}): Promise<AuthResponse> {
  const body = await request("/auth/signup", {
    method: "POST",
    body: JSON.stringify(account),
  });
  return authResponseSchema.parse(body);
}

/**
 * 저장된 토큰으로 현재 사용자를 조회한다.
 *
 * @returns 사용자 정보. 토큰이 없거나 만료돼 인증되지 않으면 `null`
 * @throws HttpError 인증 실패 외의 서버 오류
 */
export async function fetchMe(): Promise<User | null> {
  if (!getAuthToken()) return null;
  try {
    return userSchema.parse(await request("/users/me"));
  } catch (error) {
    if (error instanceof HttpError && error.status === 401) return null;
    throw error;
  }
}

/**
 * 현재 사용자의 UI 표시 언어를 변경한다.
 *
 * @param language 변경할 언어 코드
 * @returns 변경된 사용자 정보
 */
export async function updateUiLanguage(language: LanguageCode): Promise<User> {
  const body = await request("/users/me/language", {
    method: "PATCH",
    body: JSON.stringify({ language }),
  });
  return userSchema.parse(body);
}

/**
 * 현재 사용자의 비밀번호를 변경한다.
 *
 * @param passwords 현재 비밀번호와 새 비밀번호
 * @returns 사용자 정보
 * @throws HttpError 현재 비밀번호가 틀린 경우(400)
 */
export async function updatePassword(passwords: {
  currentPassword: string;
  newPassword: string;
}): Promise<User> {
  const body = await request("/users/me/password", {
    method: "PATCH",
    body: JSON.stringify(passwords),
  });
  return userSchema.parse(body);
}
