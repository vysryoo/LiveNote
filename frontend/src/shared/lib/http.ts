import { getAuthToken } from "./authToken";

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

function buildHeaders(init?: RequestInit): Headers {
  const headers = new Headers();
  // FormData는 브라우저가 boundary를 포함한 Content-Type을 직접 설정해야 함
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAuthToken();
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
 * 반환값은 검증되지 않은 값이므로 호출부에서 zod 스키마로 파싱해 사용한다.
 *
 * @param path `VITE_API_URL` 뒤에 붙는 경로. `/`로 시작해야 함
 * @param init `fetch` 옵션. `headers`는 기본 헤더를 덮어씀
 * @returns 응답 본문. 204이면 `undefined`, JSON이 아니면 `null`
 * @throws HttpError 응답 상태가 2xx가 아니거나, 감싼 응답의 `ok`가 `false`인 경우
 */
export async function request(path: string, init?: RequestInit): Promise<unknown> {
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers: buildHeaders(init) });
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
