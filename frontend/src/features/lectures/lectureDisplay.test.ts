import { describe, expect, it } from "vitest";
import { getLectureDurationMinutes, toCategoryLabel } from "./lectureDisplay";

describe("getLectureDurationMinutes", () => {
  it("생성 시각과 종료 시각의 차이를 분 단위로 내림", () => {
    expect(
      getLectureDurationMinutes({ createdAt: "2026-10-01T10:00:00", endAt: "2026-10-01T11:35:59" }),
    ).toBe(95);
  });

  it("종료되지 않은 강의는 null", () => {
    expect(getLectureDurationMinutes({ createdAt: "2026-10-01T10:00:00", endAt: null })).toBeNull();
  });

  it("해석할 수 없는 시각이나 역전된 시각은 null", () => {
    expect(
      getLectureDurationMinutes({ createdAt: "invalid", endAt: "2026-10-01T10:00:00" }),
    ).toBeNull();
    expect(
      getLectureDurationMinutes({ createdAt: "2026-10-01T11:00:00", endAt: "2026-10-01T10:00:00" }),
    ).toBeNull();
  });
});

describe("toCategoryLabel", () => {
  it("과거 오타 값을 올바른 이름으로 표시", () => {
    expect(toCategoryLabel("Econimics")).toBe("Economics");
  });

  it("그 외 값은 그대로 표시", () => {
    expect(toCategoryLabel("Physics")).toBe("Physics");
  });

  it("값이 없으면 null", () => {
    expect(toCategoryLabel(null)).toBeNull();
    expect(toCategoryLabel("")).toBeNull();
  });
});
