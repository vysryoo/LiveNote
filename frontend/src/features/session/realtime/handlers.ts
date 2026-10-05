import type { QueryClient } from "@tanstack/react-query";
import { qnaSchema, resourceSchema, type SessionDetail } from "../api/schemas";
import { sessionKeys } from "../api/sessionApi";
import type { SessionAction } from "../state/sessionReducer";
import type {
  QnaListMessage,
  ResourceListMessage,
  SectionMessage,
  StreamMessage,
  SummaryMessage,
  TranscriptMessage,
} from "./messages";

type Dispatch = (action: SessionAction) => void;

function updateDetail(
  queryClient: QueryClient,
  lectureId: number,
  update: (detail: SessionDetail) => SessionDetail,
) {
  // 상세를 아직 받기 전이면 무시. 이후 상세 조회 결과에 서버 저장분이 포함됨
  queryClient.setQueryData<SessionDetail>(sessionKeys.detail(lectureId), (detail) =>
    detail ? update(detail) : detail,
  );
}

function replaceSection<T extends { sectionIndex: number }>(
  items: T[],
  sectionIndex: number,
  next: T[],
): T[] {
  return [...items.filter((item) => item.sectionIndex !== sectionIndex), ...next];
}

function appendIfNew<T extends { id: number }>(items: T[], item: T): T[] {
  return items.some((existing) => existing.id === item.id) ? items : [...items, item];
}

/**
 * `/summary` 메시지를 해당 섹션의 요약에 반영한다. 같은 섹션의 요약이 있으면 내용을 덮어쓴다.
 *
 * @param queryClient Query 캐시
 * @param lectureId 강의 ID
 * @param message 요약 메시지
 */
export function applySummary(queryClient: QueryClient, lectureId: number, message: SummaryMessage) {
  updateDetail(queryClient, lectureId, (detail) => {
    const existing = detail.summaries.find((s) => s.sectionIndex === message.sectionIndex);
    const merged = { id: null, startSec: null, endSec: null, ...existing, ...message };
    return {
      ...detail,
      summaries: replaceSection(detail.summaries, message.sectionIndex, [merged]),
    };
  });
}

/**
 * `/qna` 메시지로 해당 섹션의 QnA 목록을 교체한다.
 *
 * @param queryClient Query 캐시
 * @param lectureId 강의 ID
 * @param message 섹션의 전체 QnA 목록
 */
export function applyQnaList(queryClient: QueryClient, lectureId: number, message: QnaListMessage) {
  updateDetail(queryClient, lectureId, (detail) => ({
    ...detail,
    qna: replaceSection(detail.qna, message.sectionIndex, message.items),
  }));
}

/**
 * `/resources` 메시지로 해당 섹션의 자료 목록을 교체한다.
 *
 * @param queryClient Query 캐시
 * @param lectureId 강의 ID
 * @param message 섹션의 전체 자료 목록
 */
export function applyResourceList(
  queryClient: QueryClient,
  lectureId: number,
  message: ResourceListMessage,
) {
  updateDetail(queryClient, lectureId, (detail) => ({
    ...detail,
    resources: replaceSection(detail.resources, message.sectionIndex, message.items),
  }));
}

/**
 * `/section` 메시지로 현재 섹션 번호를 기록한다. 현재 섹션의 유일한 쓰기 지점이다.
 *
 * @param queryClient Query 캐시
 * @param lectureId 강의 ID
 * @param message 섹션 메시지
 */
export function applySection(queryClient: QueryClient, lectureId: number, message: SectionMessage) {
  queryClient.setQueryData(sessionKeys.currentSection(lectureId), message.sectionIndex);
}

/**
 * `/transcripts` 메시지(DB에 저장된 확정 전사)를 저장된 전사 목록에 추가한다.
 *
 * @param queryClient Query 캐시
 * @param lectureId 강의 ID
 * @param message 전사 메시지
 */
export function applyTranscript(
  queryClient: QueryClient,
  lectureId: number,
  message: TranscriptMessage,
) {
  updateDetail(queryClient, lectureId, (detail) => {
    const isDuplicate = detail.transcripts.some(
      (t) =>
        t.sectionIndex === message.sectionIndex &&
        t.startSec === message.startSec &&
        t.endSec === message.endSec &&
        t.text === message.text,
    );
    return isDuplicate ? detail : { ...detail, transcripts: [...detail.transcripts, message] };
  });
}

/**
 * `/stream` 메시지를 처리한다.
 *
 * 토큰은 reducer에 쌓고, 완료되면 reducer에서 카드를 지운 뒤 완성 데이터를 Query 캐시에 추가한다.
 * 완성 데이터 형식이 맞지 않으면 캐시에 넣지 않으며, 곧 이어 오는 `/qna`·`/resources` 전체 목록으로 반영된다.
 *
 * @param queryClient Query 캐시
 * @param dispatch 세션 reducer의 dispatch
 * @param lectureId 강의 ID
 * @param message 스트리밍 메시지
 */
export function applyStream(
  queryClient: QueryClient,
  dispatch: Dispatch,
  lectureId: number,
  message: StreamMessage,
) {
  const { cardId, sectionIndex, cardIndex } = message.card;

  if (!message.isComplete) {
    dispatch({
      type: "STREAM_TOKEN",
      cardId,
      kind: message.type,
      sectionIndex,
      cardIndex,
      token: message.token,
      title: message.title ?? undefined,
      resourceType: message.resourceType ?? undefined,
    });
    return;
  }

  dispatch({ type: "STREAM_COMPLETED", cardId });
  const data = { ...message.data, sectionIndex };
  if (message.type === "qna") {
    const parsed = qnaSchema.safeParse(data);
    if (parsed.success) {
      updateDetail(queryClient, lectureId, (detail) => ({
        ...detail,
        qna: appendIfNew(detail.qna, parsed.data),
      }));
    }
  } else {
    const parsed = resourceSchema.safeParse(data);
    if (parsed.success) {
      updateDetail(queryClient, lectureId, (detail) => ({
        ...detail,
        resources: appendIfNew(detail.resources, parsed.data),
      }));
    }
  }
}

/**
 * `/error` 메시지를 처리한다. 어느 카드의 실패인지 알 수 없어 생성 중인 카드를 모두 정리한다.
 *
 * @param dispatch 세션 reducer의 dispatch
 */
export function applyStreamError(dispatch: Dispatch) {
  dispatch({ type: "STREAMS_FAILED" });
}
