export type StreamingCard = {
  cardId: string;
  kind: "qna" | "resource";
  sectionIndex: number;
  cardIndex: number;
  content: string;
  title?: string;
  resourceType?: string;
};

export type LiveTranscript = {
  // 확정된 문장들
  lines: string[];
  // 아직 말하는 중이라 다음 메시지로 교체될 문장
  pending: string | null;
};

export type SessionState = {
  streamingCards: Record<string, StreamingCard>;
  liveTranscripts: Record<number, LiveTranscript>;
};

export type SessionAction =
  | { type: "LIVE_TRANSCRIPT_RECEIVED"; sectionIndex: number; content: string; isFinal: boolean }
  | {
      type: "STREAM_TOKEN";
      cardId: string;
      kind: StreamingCard["kind"];
      sectionIndex: number;
      cardIndex: number;
      token: string;
      title?: string;
      resourceType?: string;
    }
  | { type: "STREAM_COMPLETED"; cardId: string }
  | { type: "STREAMS_FAILED" };

export const initialSessionState: SessionState = {
  streamingCards: {},
  liveTranscripts: {},
};

function mergeLiveTranscript(
  current: LiveTranscript | undefined,
  content: string,
  isFinal: boolean,
): LiveTranscript {
  const lines = current?.lines ?? [];
  // 확정 문장은 진행 중이던 문장을 대체하며 확정 목록에 들어감
  if (isFinal) return { lines: [...lines, content], pending: null };
  return { lines, pending: content };
}

/**
 * 녹음 중 실시간 전사와 생성 중인 스트리밍 카드를 관리한다.
 *
 * 서버에 완성본이 없는 데이터만 다룬다. 완성된 카드를 Query 캐시로 옮기는 일은 호출부가 수행한다.
 *
 * @param state 현재 상태
 * @param action 발생한 일
 * @returns 다음 상태
 */
export function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case "LIVE_TRANSCRIPT_RECEIVED":
      return {
        ...state,
        liveTranscripts: {
          ...state.liveTranscripts,
          [action.sectionIndex]: mergeLiveTranscript(
            state.liveTranscripts[action.sectionIndex],
            action.content,
            action.isFinal,
          ),
        },
      };

    case "STREAM_TOKEN": {
      const existing = state.streamingCards[action.cardId];
      const card: StreamingCard = {
        cardId: action.cardId,
        kind: action.kind,
        sectionIndex: action.sectionIndex,
        cardIndex: action.cardIndex,
        content: (existing?.content ?? "") + action.token,
        title: action.title ?? existing?.title,
        resourceType: action.resourceType ?? existing?.resourceType,
      };
      return { ...state, streamingCards: { ...state.streamingCards, [action.cardId]: card } };
    }

    case "STREAM_COMPLETED": {
      if (!(action.cardId in state.streamingCards)) return state;
      const streamingCards = { ...state.streamingCards };
      delete streamingCards[action.cardId];
      return { ...state, streamingCards };
    }

    case "STREAMS_FAILED":
      // 백엔드 에러 메시지에 카드 ID가 없어 생성 중인 카드를 모두 정리
      return { ...state, streamingCards: {} };
  }
}

/**
 * 한 섹션의 생성 중인 카드를 종류별로 나눠 반환한다. 화면 순서는 `orderCards`가 정한다.
 *
 * @param state 현재 상태
 * @param sectionIndex 섹션 번호. `null`이면 빈 목록
 * @returns 종류별 생성 중인 카드
 */
export function selectStreamingCards(
  state: SessionState,
  sectionIndex: number | null,
): Record<StreamingCard["kind"], StreamingCard[]> {
  const cards = Object.values(state.streamingCards).filter(
    (card) => card.sectionIndex === sectionIndex,
  );
  return {
    qna: cards.filter((card) => card.kind === "qna"),
    resource: cards.filter((card) => card.kind === "resource"),
  };
}
