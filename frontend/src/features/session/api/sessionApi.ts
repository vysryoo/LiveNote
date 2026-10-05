import { lectureKeys } from "@/features/lectures/api/lecturesApi";
import { request } from "@/shared/lib/http";
import { bookmarkSchema, sessionDetailSchema, type Bookmark, type SessionDetail } from "./schemas";

export const sessionKeys = {
  detail: lectureKeys.detail,
  currentSection: (lectureId: number) =>
    [...lectureKeys.detail(lectureId), "currentSection"] as const,
};

/**
 * 강의 상세를 전사, 요약, 자료, QnA, 북마크와 함께 조회한다.
 *
 * @param lectureId 강의 ID
 * @returns 강의 상세
 */
export async function fetchSessionDetail(lectureId: number): Promise<SessionDetail> {
  return sessionDetailSchema.parse(await request(`/lectures/${lectureId}/detail`));
}

/**
 * 저장된 데이터로 녹음이 진행된 마지막 섹션 번호를 구한다.
 *
 * 서버의 `/section` 메시지는 새 전사가 들어올 때만 오므로, 새로고침 직후에는 이 값으로 시작한다.
 *
 * @param detail 강의 상세
 * @returns 섹션 번호. 저장된 데이터가 없으면 0
 */
export function findLastSectionIndex(
  detail: Pick<SessionDetail, "transcripts" | "summaries">,
): number {
  const indexes = [...detail.transcripts, ...detail.summaries].map((item) => item.sectionIndex);
  return indexes.length === 0 ? 0 : Math.max(...indexes);
}

/**
 * 북마크를 추가한다.
 *
 * @param bookmark 북마크할 대상. 백엔드 enum에 맞춰 대상 종류는 대문자로 보냄
 * @returns 생성된 북마크
 */
export async function addBookmark(bookmark: {
  lectureId: number;
  sectionIndex: number;
  targetType: Bookmark["targetType"];
  targetId: number;
}): Promise<Bookmark> {
  const body = await request("/bookmarks", {
    method: "POST",
    body: JSON.stringify({ ...bookmark, targetType: bookmark.targetType.toUpperCase() }),
  });
  return bookmarkSchema.parse(body);
}

/**
 * 북마크를 삭제한다.
 *
 * @param bookmarkId 북마크 ID
 */
export async function deleteBookmark(bookmarkId: number): Promise<void> {
  await request(`/bookmarks/${bookmarkId}`, { method: "DELETE" });
}

/**
 * 추가 카드 하나의 스트리밍 생성을 요청한다. 결과는 `/stream` 메시지로 도착한다.
 *
 * @param card.kind 카드 종류
 * @param card.subtype QnA 유형(concept 등) 또는 자료 유형(paper 등)
 */
export async function startCardStream(card: {
  lectureId: number;
  sectionIndex: number;
  cardIndex: number;
  kind: "qna" | "resource";
  subtype: string;
}): Promise<void> {
  const params = new URLSearchParams({
    lectureId: String(card.lectureId),
    sectionIndex: String(card.sectionIndex),
    cardIndex: String(card.cardIndex),
    [card.kind === "qna" ? "qnaType" : "resourceType"]: card.subtype,
  });
  const path = card.kind === "qna" ? "/start-qna-stream" : "/start-resources-stream";
  await request(`${path}?${params.toString()}`, { method: "POST" });
}
