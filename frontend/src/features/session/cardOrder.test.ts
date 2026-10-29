import { describe, expect, it } from "vitest";
import { orderCards } from "./cardOrder";
import type { StreamingCard } from "./state/sessionReducer";

const saved = (id: number, cardId: string | null) => ({ id, cardId });
const streaming = (cardIndex: number): StreamingCard => ({
  cardId: `qna_1_0_${cardIndex}`,
  kind: "qna",
  sectionIndex: 0,
  cardIndex,
  content: "",
});
const keys = (entries: ReturnType<typeof orderCards>) => entries.map((entry) => entry.key);

describe("orderCards", () => {
  it("먼저 완성된 카드도 카드 번호 자리에 둠", () => {
    const entries = orderCards(
      [saved(10, "qna_1_0_4")],
      [streaming(2), streaming(3), streaming(5)],
    );
    expect(keys(entries)).toEqual(["qna_1_0_2", "qna_1_0_3", "saved-10", "qna_1_0_5"]);
  });

  it("카드 ID가 없는 저장 카드는 맨 앞에 원래 순서대로 둠", () => {
    const entries = orderCards(
      [saved(2, null), saved(1, null), saved(3, "qna_1_0_2")],
      [streaming(3)],
    );
    expect(keys(entries)).toEqual(["saved-2", "saved-1", "saved-3", "qna_1_0_3"]);
  });

  it("같은 카드가 저장과 생성 중 양쪽에 있으면 저장된 카드만 남김", () => {
    const entries = orderCards([saved(10, "qna_1_0_2")], [streaming(2)]);
    expect(keys(entries)).toEqual(["saved-10"]);
  });
});
