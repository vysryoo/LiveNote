import { lectureKeys } from "@/features/lectures/api/lecturesApi";
import { request } from "@/shared/lib/http";
import { sessionDetailSchema, type SessionDetail } from "./schemas";

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
