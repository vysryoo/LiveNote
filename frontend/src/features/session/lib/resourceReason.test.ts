import { describe, expect, it } from "vitest";
import { toDisplayReason } from "./resourceReason";

describe("toDisplayReason", () => {
  it("LLM이 쓴 추천 이유는 그대로 보여 줌", () => {
    expect(toDisplayReason(" 이 논문은 스택 구조를 직접 다룹니다. ")).toBe(
      "이 논문은 스택 구조를 직접 다룹니다.",
    );
  });

  it("비어 있으면 숨김", () => {
    expect(toDisplayReason(null)).toBeNull();
    expect(toDisplayReason(undefined)).toBeNull();
    expect(toDisplayReason("   ")).toBeNull();
  });

  it("AI 서버의 자리 표시 값은 대소문자와 관계없이 숨김", () => {
    for (const reason of [
      "search",
      "Heuristic",
      "검증 완료",
      "LLM evaluation",
      "LLM verification",
      "Scoring failed",
      "Parsing failed",
      "Aligned with key terms (stub).",
    ]) {
      expect(toDisplayReason(reason)).toBeNull();
    }
  });

  it("검증 실패 문구는 괄호 안 사유와 관계없이 숨김", () => {
    expect(toDisplayReason("검증 실패")).toBeNull();
    expect(toDisplayReason("검증 실패 (JSON 파싱 오류)")).toBeNull();
    expect(toDisplayReason("검증 실패 (fallback)")).toBeNull();
  });
});
