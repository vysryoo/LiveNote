import { z } from "zod";
import { request } from "@/shared/lib/http";
import type { LanguageCode } from "@/shared/i18n";
import { lectureSchema, type Lecture } from "./schemas";

export const lectureKeys = {
  list: ["lectures", "list"] as const,
  detail: (lectureId: number) => ["lectures", "detail", lectureId] as const,
};

/**
 * 로그인한 사용자의 강의 목록을 조회한다.
 *
 * @returns 최신순으로 정렬된 강의 목록. 백엔드가 최근 20개까지만 반환함
 */
export async function fetchLectures(): Promise<Lecture[]> {
  return z.array(lectureSchema).parse(await request("/lectures"));
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
 * 강의를 종료 상태로 바꾼다.
 *
 * @param lectureId 강의 ID
 * @returns 종료된 강의
 */
export async function endLecture(lectureId: number): Promise<Lecture> {
  return lectureSchema.parse(await request(`/lectures/${lectureId}/end`, { method: "POST" }));
}
