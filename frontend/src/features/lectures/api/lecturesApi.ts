import { request } from "@/shared/lib/http";
import type { LanguageCode } from "@/shared/i18n";
import { lecturePageSchema, lectureSchema, type Lecture, type LecturePage } from "./schemas";

export const lectureKeys = {
  list: ["lectures", "list"] as const,
  detail: (lectureId: number) => ["lectures", "detail", lectureId] as const,
};

export const LECTURE_PAGE_SIZE = 20;

/**
 * 로그인한 사용자의 강의 목록 한 페이지를 조회한다.
 *
 * @param page 0부터 시작하는 페이지 번호
 * @returns 최신순 강의 목록, 전체 강의 수, 다음 페이지 여부
 */
export async function fetchLecturePage(page: number): Promise<LecturePage> {
  const params = new URLSearchParams({ page: String(page), size: String(LECTURE_PAGE_SIZE) });
  return lecturePageSchema.parse(await request(`/lectures?${params.toString()}`));
}

/**
 * 새 강의를 생성한다.
 *
 * 자료 파일이 있으면 multipart로 보내 백엔드가 RAG 업서트까지 수행한다.
 *
 * @param lecture.title 과목명
 * @param lecture.subject 분야
 * @param lecture.sttLanguage 음성 인식 언어
 * @param lecture.file 참고 자료 PDF. 없으면 JSON으로 생성
 * @returns 생성된 강의
 * @throws HttpError PDF가 아닌 파일을 보낸 경우(400)
 */
export async function createLecture(lecture: {
  title: string;
  subject: string;
  sttLanguage: LanguageCode;
  file?: File;
}): Promise<Lecture> {
  const { file, ...fields } = lecture;
  let body: BodyInit = JSON.stringify(fields);
  if (file) {
    const formData = new FormData();
    Object.entries(fields).forEach(([key, value]) => formData.append(key, value));
    formData.append("files", file);
    body = formData;
  }
  return lectureSchema.parse(await request("/lectures", { method: "POST", body }));
}

/**
 * 강의 제목을 변경한다.
 *
 * @param lectureId 강의 ID
 * @param title 새 제목
 * @returns 변경된 강의
 */
export async function updateLectureTitle(lectureId: number, title: string): Promise<Lecture> {
  const body = await request(`/lectures/${lectureId}/title`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
  return lectureSchema.parse(body);
}

/**
 * 강의와 관련 데이터를 삭제한다.
 *
 * @param lectureId 강의 ID
 */
export async function deleteLecture(lectureId: number): Promise<void> {
  await request(`/lectures/${lectureId}`, { method: "DELETE" });
}

/**
 * 강의를 종료 상태로 바꾸고 제목을 함께 저장한다.
 *
 * @param lectureId 강의 ID
 * @param title 저장할 제목. 비어 있으면 백엔드가 기존 제목을 유지함
 * @returns 종료된 강의
 */
export async function endLecture(lectureId: number, title: string): Promise<Lecture> {
  const body = await request(`/lectures/${lectureId}/end`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  return lectureSchema.parse(body);
}
