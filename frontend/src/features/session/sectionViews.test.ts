import { describe, expect, it } from "vitest";
import type { Summary, Transcript } from "./api/schemas";
import { buildSectionViews, mergeTranscriptLines } from "./sectionViews";

function transcript(sectionIndex: number, text: string): Transcript {
  return { sectionIndex, startSec: 0, endSec: 0, text };
}

function summary(sectionIndex: number, text: string, phase: Summary["phase"]): Summary {
  return { id: sectionIndex + 1, sectionIndex, startSec: 0, endSec: 30, text, phase };
}

const base = {
  transcripts: [],
  summaries: [],
  liveTranscripts: {},
  currentSection: 0,
  isRecording: false,
  selectedSectionIndex: null,
  autoMode: false,
};

describe("mergeTranscriptLines", () => {
  it("실시간 확정 문장 중 이미 저장된 것은 한 번만 표시", () => {
    expect(
      mergeTranscriptLines(["첫 문장"], { lines: ["첫 문장", "둘째 문장"], pending: null }),
    ).toEqual(["첫 문장", "둘째 문장"]);
  });

  it("새로고침 전 저장된 문장과 이후 실시간 문장을 모두 표시", () => {
    expect(
      mergeTranscriptLines(["이전 문장"], { lines: ["새 문장"], pending: "말하는 중" }),
    ).toEqual(["이전 문장", "새 문장", "말하는 중"]);
  });

  it("같은 문장이 두 번 말해지면 두 번 표시", () => {
    expect(mergeTranscriptLines(["반복"], { lines: ["반복", "반복"], pending: null })).toEqual([
      "반복",
      "반복",
    ]);
  });

  it("실시간 전사가 없으면 저장본만", () => {
    expect(mergeTranscriptLines([" 문장 ", ""])).toEqual(["문장"]);
  });
});

describe("buildSectionViews", () => {
  it("전사, 요약, 실시간 전사가 있는 섹션을 오름차순으로 표시", () => {
    const views = buildSectionViews({
      ...base,
      transcripts: [transcript(2, "c")],
      summaries: [summary(0, "a", "final")],
      liveTranscripts: { 1: { lines: ["b"], pending: null } },
    });
    expect(views.map((v) => v.sectionIndex)).toEqual([0, 1, 2]);
  });

  it("녹음 중이면 데이터가 없어도 현재 섹션을 표시", () => {
    const views = buildSectionViews({ ...base, isRecording: true, currentSection: 3 });
    expect(views).toEqual([expect.objectContaining({ sectionIndex: 3, isCurrent: true })]);
  });

  it("녹음 중이 아니면 현재 섹션 표시를 하지 않음", () => {
    const views = buildSectionViews({ ...base, transcripts: [transcript(0, "a")] });
    expect(views[0].isCurrent).toBe(false);
  });

  it("확정 요약만 선택 가능하고 부분 요약은 선택 불가", () => {
    const views = buildSectionViews({
      ...base,
      summaries: [summary(0, "확정", "final"), summary(1, "부분", "partial")],
    });
    expect(views.map((v) => v.isClickable)).toEqual([true, false]);
  });

  it("오토 모드 중에는 직접 선택 불가", () => {
    const views = buildSectionViews({
      ...base,
      autoMode: true,
      summaries: [summary(0, "확정", "final")],
    });
    expect(views[0].isClickable).toBe(false);
  });

  it("선택된 섹션 표시", () => {
    const views = buildSectionViews({
      ...base,
      selectedSectionIndex: 1,
      summaries: [summary(0, "a", "final"), summary(1, "b", "final")],
    });
    expect(views.map((v) => v.isSelected)).toEqual([false, true]);
  });
});
