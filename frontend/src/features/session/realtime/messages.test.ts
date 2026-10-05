import { describe, expect, it } from "vitest";
import {
  audioSocketMessageSchema,
  parseCardId,
  streamMessageSchema,
  summaryMessageSchema,
} from "./messages";

describe("parseCardId", () => {
  it("접두사와 관계없이 섹션 번호와 카드 번호를 꺼냄", () => {
    expect(parseCardId("qna_7_3_2")).toEqual({ sectionIndex: 3, cardIndex: 2 });
    expect(parseCardId("res_7_3_4")).toEqual({ sectionIndex: 3, cardIndex: 4 });
    expect(parseCardId("resource_7_0_5")).toEqual({ sectionIndex: 0, cardIndex: 5 });
  });

  it("형식이 다르면 null", () => {
    expect(parseCardId("qna_7_3")).toBeNull();
    expect(parseCardId("qna_a_b_c")).toBeNull();
  });
});

describe("streamMessageSchema", () => {
  it("토큰 메시지에서 카드 종류와 섹션 번호를 구함", () => {
    const parsed = streamMessageSchema.parse({
      type: "resource_stream",
      cardId: "res_7_3_4",
      isComplete: false,
      token: "가",
      title: "논문 제목",
      resourceType: "paper",
    });
    expect(parsed).toMatchObject({
      type: "resource",
      card: { cardId: "res_7_3_4", sectionIndex: 3, cardIndex: 4 },
      token: "가",
    });
  });

  it("완료 메시지는 data를 그대로 담음", () => {
    const parsed = streamMessageSchema.parse({
      type: "qna_stream",
      cardId: "qna_7_1_2",
      isComplete: true,
      data: { id: 10, type: "concept", question: "Q", answer: "A" },
    });
    expect(parsed.isComplete).toBe(true);
    expect(parsed.type).toBe("qna");
  });

  it("카드 ID 형식이 다르면 거부", () => {
    const result = streamMessageSchema.safeParse({
      type: "qna_stream",
      cardId: "broken",
      isComplete: false,
      token: "a",
    });
    expect(result.success).toBe(false);
  });
});

describe("summaryMessageSchema", () => {
  it("소문자 phase를 받음", () => {
    expect(
      summaryMessageSchema.parse({
        type: "summary",
        lectureId: 7,
        sectionIndex: 1,
        text: "요약",
        phase: "final",
      }),
    ).toEqual({ sectionIndex: 1, text: "요약", phase: "final" });
  });
});

describe("audioSocketMessageSchema", () => {
  it("전사 메시지의 isFinal이 없으면 false", () => {
    expect(
      audioSocketMessageSchema.parse({ type: "transcript", data: { content: "안녕" } }),
    ).toEqual({ type: "transcript", data: { content: "안녕", isFinal: false } });
  });
});
