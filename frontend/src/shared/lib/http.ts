import { clearAuthToken, getAuthToken, setAuthToken } from "./authToken";

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export class HttpError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "HttpError";
  }
}

// 만료 직전 토큰으로 요청하면 도중에 거부될 수 있어 이만큼 남았을 때 미리 갱신
const REFRESH_MARGIN_MS = 60_000;

let refreshInFlight: Promise<string | null> | null = null;
const sessionExpiredListeners = new Set<() => void>();

function readExpiry(token: string): number | null {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const { exp } = JSON.parse(atob(payload)) as { exp?: unknown };
    return typeof exp === "number" ? exp * 1000 : null;
  } catch {
    return null;
  }
}

/**
 * 갱신 토큰 쿠키로 새 접근 토큰을 받아 저장한다.
 *
 * 갱신 토큰은 한 번 쓰면 교체되므로, 동시에 여러 곳에서 호출해도 요청은 한 번만 보내고 결과를 공유한다.
 * 갱신에 실패하면 저장된 토큰을 지우고 `onSessionExpired`로 등록한 함수를 호출한다.
 *
 * @returns 새 접근 토큰. 갱신 토큰이 없거나 만료됐으면 `null`
 */
export function refreshAccessToken(): Promise<string | null> {
  refreshInFlight ??= (async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      const body = res.ok ? parseJson(await res.text()) : null;
      const token = isEnvelope(body) && body.ok ? (body.data as { token?: unknown })?.token : null;
      if (typeof token === "string" && token) {
        setAuthToken(token);
        return token;
      }
    } catch {
      // 네트워크 오류도 갱신 실패로 처리
    }
    clearAuthToken();
    sessionExpiredListeners.forEach((listener) => listener());
    return null;
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

/**
 * 만료가 임박하지 않은 접근 토큰을 반환한다. 곧 만료되면 먼저 갱신한다.
 *
 * 연결할 때만 토큰을 확인하는 WebSocket·STOMP 연결 직전에 사용한다.
 *
 * @returns 접근 토큰. 로그인하지 않았거나 갱신에 실패하면 `null`
 */
export async function getFreshAuthToken(): Promise<string | null> {
  const token = getAuthToken();
  if (!token) return null;
  const expiresAt = readExpiry(token);
  if (expiresAt !== null && expiresAt - Date.now() < REFRESH_MARGIN_MS) {
    return refreshAccessToken();
  }
  return token;
}

/**
 * 로그인 세션이 끝났을 때(갱신 실패) 호출할 함수를 등록한다.
 *
 * @param listener 세션 만료 시 호출할 함수
 * @returns 등록 해제 함수
 */
export function onSessionExpired(listener: () => void): () => void {
  sessionExpiredListeners.add(listener);
  return () => {
    sessionExpiredListeners.delete(listener);
  };
}

function buildHeaders(init: RequestInit | undefined, token: string | null): Headers {
  const headers = new Headers();
  // FormData는 브라우저가 boundary를 포함한 Content-Type을 직접 설정해야 함
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  new Headers(init?.headers).forEach((value, key) => headers.set(key, value));
  return headers;
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function extractErrorMessage(body: string, fallback: string): string {
  const parsed = parseJson(body);
  if (typeof parsed === "string" && parsed) return parsed;
  if (parsed && typeof parsed === "object" && "message" in parsed && parsed.message) {
    return String(parsed.message);
  }
  return body || fallback;
}

function isEnvelope(body: unknown): body is { ok: boolean; data: unknown; message?: string } {
  return typeof body === "object" && body !== null && "ok" in body && "data" in body;
}

/**
 * 백엔드 API를 호출하고 응답 본문을 반환한다.
 *
 * `{ ok, data, message }` 형태로 감싼 응답은 `data`만 꺼내 반환한다.
 * 접근 토큰이 만료돼 401을 받으면 갱신 토큰으로 새 토큰을 받아 한 번 다시 요청한다(`/auth/*` 제외).
 * 반환값은 검증되지 않은 값이므로 호출부에서 zod 스키마로 파싱해 사용한다.
 *
 * @param path `VITE_API_URL` 뒤에 붙는 경로. `/`로 시작해야 함
 * @param init `fetch` 옵션. `headers`는 기본 헤더를 덮어씀
 * @returns 응답 본문. 204이면 `undefined`, JSON이 아니면 `null`
 * @throws HttpError 응답 상태가 2xx가 아니거나, 감싼 응답의 `ok`가 `false`인 경우. 갱신에 실패한 401 포함
 */
export async function request(path: string, init?: RequestInit): Promise<unknown> {
  const isAuthPath = path.startsWith("/auth/");
  const token = isAuthPath ? getAuthToken() : await getFreshAuthToken();
  const send = (accessToken: string | null) =>
    fetch(`${API_BASE}${path}`, {
      ...init,
      headers: buildHeaders(init, accessToken),
      // 로그인·갱신 응답의 갱신 토큰 쿠키를 받고 보내기 위함
      credentials: "include",
    });

  let res = await send(token);
  if (res.status === 401 && token && !isAuthPath) {
    const refreshed = await refreshAccessToken();
    if (refreshed) res = await send(refreshed);
  }
  const text = res.status === 204 ? "" : await res.text();

  if (!res.ok) {
    throw new HttpError(
      res.status,
      extractErrorMessage(text, `HTTP ${res.status} ${res.statusText}`),
    );
  }
  if (res.status === 204) return undefined;

  const body = parseJson(text);
  if (isEnvelope(body)) {
    if (body.ok) return body.data;
    throw new HttpError(res.status, body.message || "Request failed");
  }
  return body;
}
