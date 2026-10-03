const TOKEN_KEY = "SPRING_TOKEN";

// localStorage를 쓸 수 없는 환경에서도 새로고침 전까지는 로그인을 유지하기 위한 사본
let tokenInMemory: string | null = null;

function isUsableToken(token: string | null | undefined): token is string {
  // 잘못된 대입으로 문자열 'undefined', 'null'이 저장될 수 있어 토큰으로 취급하지 않음
  return !!token && token !== "undefined" && token !== "null";
}

/**
 * 저장된 로그인 토큰을 반환한다.
 *
 * @returns 토큰. 없거나 유효하지 않은 값이면 `null`
 */
export function getAuthToken(): string | null {
  if (isUsableToken(tokenInMemory)) return tokenInMemory;
  try {
    const stored = globalThis.localStorage?.getItem(TOKEN_KEY);
    return isUsableToken(stored) ? stored : null;
  } catch {
    return null;
  }
}

/**
 * 로그인 토큰을 메모리와 localStorage에 저장한다.
 *
 * @param token 백엔드가 발급한 JWT
 */
export function setAuthToken(token: string): void {
  tokenInMemory = token;
  try {
    globalThis.localStorage?.setItem(TOKEN_KEY, token);
  } catch {
    // 프라이빗 모드 등 localStorage 접근 불가 환경은 메모리 사본만 사용
  }
}

/**
 * 저장된 로그인 토큰을 메모리와 localStorage에서 삭제한다.
 */
export function clearAuthToken(): void {
  tokenInMemory = null;
  try {
    globalThis.localStorage?.removeItem(TOKEN_KEY);
  } catch {
    // 프라이빗 모드 등 localStorage 접근 불가 환경
  }
}
