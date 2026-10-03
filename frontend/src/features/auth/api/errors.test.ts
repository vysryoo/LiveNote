import { describe, expect, it } from "vitest";
import { HttpError } from "@/shared/lib/http";
import { toAuthErrorKey } from "./errors";

describe("toAuthErrorKey", () => {
  it("아이디 없음과 비밀번호 틀림을 같은 문구로 변환", () => {
    expect(toAuthErrorKey(new HttpError(404, "no user"))).toBe("auth.errors.badCredential");
    expect(toAuthErrorKey(new HttpError(400, "bad credential"))).toBe("auth.errors.badCredential");
  });

  it("중복 아이디와 중복 이메일을 구분해 변환", () => {
    expect(toAuthErrorKey(new HttpError(400, "duplicated loginId"))).toBe(
      "auth.errors.duplicatedLoginId",
    );
    expect(toAuthErrorKey(new HttpError(400, "duplicated email"))).toBe(
      "auth.errors.duplicatedEmail",
    );
  });

  it("알 수 없는 서버 메시지는 일반 실패 문구로 변환", () => {
    expect(toAuthErrorKey(new HttpError(500, "server error"))).toBe("common.requestFailed");
  });

  it("HttpError가 아닌 에러는 일반 실패 문구로 변환", () => {
    expect(toAuthErrorKey(new TypeError("Failed to fetch"))).toBe("common.requestFailed");
  });
});
