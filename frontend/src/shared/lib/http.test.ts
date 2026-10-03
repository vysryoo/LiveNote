import { afterEach, describe, expect, it, vi } from "vitest";
import { HttpError, request } from "./http";

function mockFetch(response: Response) {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

function sentHeaders(fetchMock: ReturnType<typeof vi.fn>): Headers {
  return fetchMock.mock.calls[0][1].headers;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("request", () => {
  it("감싼 응답에서 data만 반환", async () => {
    mockFetch(jsonResponse({ ok: true, data: { id: 1 }, message: "" }));
    await expect(request("/lectures")).resolves.toEqual({ id: 1 });
  });

  it("감싸지 않은 응답은 그대로 반환", async () => {
    mockFetch(jsonResponse([{ id: 1 }]));
    await expect(request("/lectures")).resolves.toEqual([{ id: 1 }]);
  });

  it("204 응답은 undefined 반환", async () => {
    mockFetch(new Response(null, { status: 204 }));
    await expect(request("/lectures/1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("JSON이 아닌 응답 본문은 null 반환", async () => {
    mockFetch(new Response("plain", { status: 200 }));
    await expect(request("/health")).resolves.toBeNull();
  });

  it("감싼 응답의 ok가 false면 message로 HttpError 발생", async () => {
    mockFetch(jsonResponse({ ok: false, data: null, message: "중복된 아이디" }));
    await expect(request("/auth/signup")).rejects.toEqual(new HttpError(200, "중복된 아이디"));
  });

  it("에러 응답의 message 필드를 에러 메시지로 사용", async () => {
    mockFetch(jsonResponse({ message: "비밀번호 불일치" }, 401));
    const error = await request("/auth/login").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(HttpError);
    expect(error).toMatchObject({ status: 401, message: "비밀번호 불일치" });
  });

  it("JSON이 아닌 에러 응답은 본문 텍스트를 에러 메시지로 사용", async () => {
    mockFetch(new Response("Bad Gateway", { status: 502 }));
    await expect(request("/lectures")).rejects.toMatchObject({
      status: 502,
      message: "Bad Gateway",
    });
  });

  it("본문 없는 에러 응답은 상태 코드로 에러 메시지 구성", async () => {
    mockFetch(new Response("", { status: 500, statusText: "Internal Server Error" }));
    await expect(request("/lectures")).rejects.toMatchObject({
      message: "HTTP 500 Internal Server Error",
    });
  });

  it("저장된 토큰을 Authorization 헤더로 전송", async () => {
    vi.stubGlobal("localStorage", { getItem: () => "abc" });
    const fetchMock = mockFetch(jsonResponse({}));
    await request("/auth/me");
    expect(sentHeaders(fetchMock).get("Authorization")).toBe("Bearer abc");
  });

  it("문자열 'undefined' 토큰은 전송하지 않음", async () => {
    vi.stubGlobal("localStorage", { getItem: () => "undefined" });
    const fetchMock = mockFetch(jsonResponse({}));
    await request("/auth/me");
    expect(sentHeaders(fetchMock).has("Authorization")).toBe(false);
  });

  it("FormData 본문에는 Content-Type을 설정하지 않음", async () => {
    const fetchMock = mockFetch(jsonResponse({}));
    await request("/lectures", { method: "POST", body: new FormData() });
    expect(sentHeaders(fetchMock).has("Content-Type")).toBe(false);
  });
});
