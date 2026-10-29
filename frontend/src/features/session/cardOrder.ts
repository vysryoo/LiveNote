import { parseCardId } from "./realtime/messages";
import type { StreamingCard } from "./state/sessionReducer";

export type CardEntry<T> =
  { kind: "saved"; key: string; item: T } | { kind: "streaming"; key: string; card: StreamingCard };

/**
 * 저장된 카드와 생성 중인 카드를 카드 번호 순으로 합친다.
 *
 * 생성은 동시에 진행되어 완료 순서가 카드 번호 순서와 다르므로, 따로 그리면 먼저 끝난 카드가 위로 올라간다.
 * 카드 ID가 없는 저장 카드는 맨 앞에 원래 순서대로 둔다. 같은 카드 ID가 양쪽에 있으면 저장된 카드만 남긴다.
 *
 * @param saved 저장된 카드 목록
 * @param streaming 생성 중인 카드 목록
 * @returns 화면에 그릴 순서의 카드 목록
 */
export function orderCards<T extends { id: number; cardId?: string | null }>(
  saved: T[],
  streaming: StreamingCard[],
): CardEntry<T>[] {
  const savedCardIds = new Set(saved.map((item) => item.cardId).filter(Boolean));
  const entries = [
    ...saved.map((item) => ({
      index: (item.cardId ? parseCardId(item.cardId)?.cardIndex : undefined) ?? -1,
      entry: { kind: "saved", key: `saved-${item.id}`, item } as CardEntry<T>,
    })),
    ...streaming
      .filter((card) => !savedCardIds.has(card.cardId))
      .map((card) => ({
        index: card.cardIndex,
        entry: { kind: "streaming", key: card.cardId, card } as CardEntry<T>,
      })),
  ];
  // Array.prototype.sort는 안정 정렬이라 번호가 같거나 없는 카드는 원래 순서를 유지함
  return entries.sort((a, b) => a.index - b.index).map(({ entry }) => entry);
}
