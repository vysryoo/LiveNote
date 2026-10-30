import { describe, expect, it } from "vitest";
import {
  initialSessionState,
  selectStreamingCards,
  sessionReducer,
  type SessionAction,
  type SessionState,
} from "./sessionReducer";

function reduce(actions: SessionAction[], state: SessionState = initialSessionState) {
  return actions.reduce(sessionReducer, state);
}

function transcript(sectionIndex: number, content: string, isFinal: boolean): SessionAction {
  return { type: "LIVE_TRANSCRIPT_RECEIVED", sectionIndex, content, isFinal };
}

function token(cardId: string, text: string, extra: Partial<SessionAction> = {}): SessionAction {
  return {
    type: "STREAM_TOKEN",
    cardId,
    kind: "qna",
    sectionIndex: 1,
    cardIndex: 2,
    token: text,
    ...extra,
  } as SessionAction;
}

describe("LIVE_TRANSCRIPT_RECEIVED", () => {
  it("확정 문장을 순서대로 쌓음", () => {
    const state = reduce([transcript(0, "첫 문장", true), transcript(0, "둘째 문장", true)]);
    expect(state.liveTranscripts[0]).toEqual({ lines: ["첫 문장", "둘째 문장"], pending: null });
  });

  it("진행 중 문장은 다음 진행 중 문장으로 교체", () => {
    const state = reduce([transcript(0, "안", false), transcript(0, "안녕", false)]);
    expect(state.liveTranscripts[0]).toEqual({ lines: [], pending: "안녕" });
  });

  it("확정 문장이 오면 진행 중 문장을 대체하고 중복 줄을 남기지 않음", () => {
    const state = reduce([
      transcript(0, "첫 문장", true),
      transcript(0, "안녕", false),
      transcript(0, "안녕하세요", true),
    ]);
    expect(state.liveTranscripts[0]).toEqual({ lines: ["첫 문장", "안녕하세요"], pending: null });
  });

  it("확정 문장 뒤의 진행 중 문장은 확정 문장을 덮지 않음", () => {
    const state = reduce([transcript(0, "첫 문장", true), transcript(0, "둘", false)]);
    expect(state.liveTranscripts[0]).toEqual({ lines: ["첫 문장"], pending: "둘" });
  });

  it("섹션별로 따로 쌓음", () => {
    const state = reduce([transcript(0, "영", true), transcript(1, "일", true)]);
    expect(state.liveTranscripts[0]).toEqual({ lines: ["영"], pending: null });
    expect(state.liveTranscripts[1]).toEqual({ lines: ["일"], pending: null });
  });
});

describe("STREAM_TOKEN", () => {
  it("첫 토큰으로 카드를 만들고 이후 토큰을 이어 붙임", () => {
    const state = reduce([token("qna_7_1_2", "질"), token("qna_7_1_2", "문")]);
    expect(state.streamingCards["qna_7_1_2"]).toMatchObject({
      kind: "qna",
      sectionIndex: 1,
      cardIndex: 2,
      content: "질문",
    });
  });

  it("제목과 자료 유형은 새 값이 없으면 이전 값을 유지", () => {
    const state = reduce([
      token("res_7_1_3", "a", { kind: "resource", title: "논문", resourceType: "paper" }),
      token("res_7_1_3", "b", { kind: "resource" }),
    ]);
    expect(state.streamingCards["res_7_1_3"]).toMatchObject({
      title: "논문",
      resourceType: "paper",
      content: "ab",
    });
  });
});

describe("STREAM_COMPLETED", () => {
  it("완료된 카드만 제거", () => {
    const state = reduce([
      token("qna_7_1_2", "a"),
      token("qna_7_1_3", "b"),
      { type: "STREAM_COMPLETED", cardId: "qna_7_1_2" },
    ]);
    expect(Object.keys(state.streamingCards)).toEqual(["qna_7_1_3"]);
  });

  it("없는 카드면 상태를 그대로 반환", () => {
    const before = reduce([token("qna_7_1_2", "a")]);
    expect(sessionReducer(before, { type: "STREAM_COMPLETED", cardId: "none" })).toBe(before);
  });
});

describe("STREAMS_FAILED", () => {
  it("생성 중인 카드를 모두 정리하고 실시간 전사는 유지", () => {
    const state = reduce([
      transcript(0, "문장", true),
      token("qna_7_1_2", "a"),
      token("res_7_1_3", "b", { kind: "resource" }),
      { type: "STREAMS_FAILED" },
    ]);
    expect(state.streamingCards).toEqual({});
    expect(state.liveTranscripts[0]).toEqual({ lines: ["문장"], pending: null });
  });
});

describe("selectStreamingCards", () => {
  it("선택한 섹션의 카드만 종류별로 나눔", () => {
    const state = reduce([
      token("qna_7_1_2", "a"),
      token("res_7_1_3", "b", { kind: "resource" }),
      token("qna_7_2_2", "c", { sectionIndex: 2 }),
    ]);
    const cards = selectStreamingCards(state, 1);
    expect(cards.qna.map((card) => card.cardId)).toEqual(["qna_7_1_2"]);
    expect(cards.resource.map((card) => card.cardId)).toEqual(["res_7_1_3"]);
  });

  it("섹션을 선택하지 않았으면 빈 목록", () => {
    const state = reduce([token("qna_7_1_2", "a")]);
    expect(selectStreamingCards(state, null)).toEqual({ qna: [], resource: [] });
  });
});

describe("순수성", () => {
  it("같은 입력에 같은 결과를 내고 이전 상태를 바꾸지 않음", () => {
    const before = reduce([token("qna_7_1_2", "a")]);
    const snapshot = structuredClone(before);
    const action = token("qna_7_1_2", "b");
    expect(sessionReducer(before, action)).toEqual(sessionReducer(before, action));
    expect(before).toEqual(snapshot);
  });
});
