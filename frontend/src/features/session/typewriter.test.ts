import { describe, expect, it } from "vitest";
import { advanceReveal } from "./typewriter";

describe("advanceReveal", () => {
  it("한 번에 정해진 글자 수만큼 늘림", () => {
    expect(advanceReveal(0, 100, 5)).toBe(5);
    expect(advanceReveal(5, 100, 5)).toBe(10);
  });

  it("전체 글자 수를 넘지 않음", () => {
    expect(advanceReveal(98, 100, 5)).toBe(100);
    expect(advanceReveal(100, 100, 5)).toBe(100);
  });

  it("328자 답변은 66번 만에 다 보임 (초당 100자 기준 약 3.3초)", () => {
    let shown = 0;
    let ticks = 0;
    while (shown < 328) {
      shown = advanceReveal(shown, 328);
      ticks += 1;
    }
    expect(ticks).toBe(66);
  });
});
