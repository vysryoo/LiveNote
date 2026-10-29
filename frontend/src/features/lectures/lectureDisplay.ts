import type { Lecture, LecturePage } from "./api/schemas";

export const LECTURE_CATEGORIES = [
  "Computer Science",
  "Mathematics",
  "Physics",
  "Chemistry",
  "Biology",
  "Economics",
  "Others",
] as const;

// 과거 분야 선택지의 값 오타로 DB에 저장된 값
const LEGACY_CATEGORY_ALIASES: Record<string, string> = {
  Econimics: "Economics",
};

/**
 * 저장된 분야 값을 화면 표시용 이름으로 바꾼다.
 *
 * @param subject 강의의 분야 값
 * @returns 표시할 분야 이름. 값이 없으면 `null`
 */
export function toCategoryLabel(subject: string | null): string | null {
  if (!subject) return null;
  return LEGACY_CATEGORY_ALIASES[subject] ?? subject;
}

/**
 * 강의 생성부터 종료까지 걸린 시간을 분 단위로 계산한다.
 *
 * 백엔드가 녹음 시간을 따로 저장하지 않아 생성 시각과 종료 시각의 차이로 계산한다.
 *
 * @param lecture 강의
 * @returns 경과 분. 종료되지 않았거나 시각을 해석할 수 없으면 `null`
 */
export function getLectureDurationMinutes(
  lecture: Pick<Lecture, "createdAt" | "endAt">,
): number | null {
  if (!lecture.endAt) return null;
  const elapsedMs = new Date(lecture.endAt).getTime() - new Date(lecture.createdAt).getTime();
  if (Number.isNaN(elapsedMs) || elapsedMs < 0) return null;
  return Math.floor(elapsedMs / 60_000);
}

/**
 * 여러 페이지로 받은 강의 목록을 하나로 합친다.
 *
 * 페이지를 받는 사이 강의가 추가·삭제되면 같은 강의가 두 페이지에 걸쳐 올 수 있어, 먼저 나온 것만 남긴다.
 *
 * @param pages 받은 순서대로의 페이지 목록
 * @returns 중복 없는 강의 목록
 */
export function mergeLecturePages(pages: LecturePage[]): Lecture[] {
  const seen = new Set<number>();
  return pages
    .flatMap((page) => page.items)
    .filter((lecture) => {
      if (seen.has(lecture.id)) return false;
      seen.add(lecture.id);
      return true;
    });
}
