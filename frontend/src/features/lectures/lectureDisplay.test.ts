import { describe, expect, it } from "vitest";
import { getLectureDurationMinutes, mergeLecturePages, toCategoryLabel } from "./lectureDisplay";

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

describe("mergeLecturePages", () => {
  const lecture = (id: number) => ({
    id,
    userId: 1,
    title: `강의 ${id}`,
    subject: null,
    sttLanguage: "ko",
    status: "COMPLETED" as const,
    createdAt: "2026-10-01T10:00:00",
    endAt: null,
  });

  it("페이지 순서대로 이어 붙임", () => {
    const pages = [
      { items: [lecture(3), lecture(2)], total: 3, hasNext: true },
      { items: [lecture(1)], total: 3, hasNext: false },
    ];
    expect(mergeLecturePages(pages).map((l) => l.id)).toEqual([3, 2, 1]);
  });

  it("페이지 사이에 밀려 다시 온 강의는 한 번만 남김", () => {
    const pages = [
      { items: [lecture(3), lecture(2)], total: 3, hasNext: true },
      { items: [lecture(2), lecture(1)], total: 4, hasNext: false },
    ];
    expect(mergeLecturePages(pages).map((l) => l.id)).toEqual([3, 2, 1]);
  });
});
