// @ts-nocheck: 미사용 어댑터, Phase 3(폴더 재구성)에서 삭제 예정 — 타입 정합성 작업 생략
import type {
  AuthPort,
  BackendPort,
  Bookmark,
  BookmarkRequest,
  CreateLectureRequest,
  Lecture,
  LecturePort,
  LoginRequest,
  AuthResponse,
  SessionDetailResponse,
  SetLanguageRequest,
  SetPasswordRequest,
  SettingsPort,
  Summary,
  Transcript,
  QnA,
  Resource,
  UpdateLectureTitleRequest,
  UserView,
} from "../ports";

// Supabase REST (PostgREST) 엔드포인트 사용. DB SDK 의존 없이 HTTP만 사용
const API_URL = (import.meta as any).env?.VITE_API_URL as string; // e.g. https://project.supabase.co
const PUBLIC_KEY = (import.meta as any).env?.VITE_PUBLIC_KEY as string;
const REST_BASE = API_URL ? `${API_URL}/rest/v1` : "/supabase/rest/v1";
const WS_BASE = (import.meta as any).env?.VITE_WS_URL || "ws://localhost:8080";
let currentUserId: number | null = null;

function baseHeaders() {
  return {
    apikey: PUBLIC_KEY,
    Authorization: `Bearer ${PUBLIC_KEY}`,
    "Content-Type": "application/json",
    Prefer: "return=representation",
  } as Record<string, string>;
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData를 사용하는 경우 Content-Type을 설정하지 않음 (브라우저가 자동으로 boundary 설정)
  const isFormData = init?.body instanceof FormData;
  const base = { ...baseHeaders() };
  // FormData인 경우 Content-Type 제거
  if (isFormData) {
    delete (base as any)["Content-Type"];
  }
  const headers = { ...base, ...(init?.headers || {}) };
  const res = await fetch(`${REST_BASE}${path}`, { headers, ...init });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return (await res.json()) as T;
}

async function getCurrentUser(): Promise<UserView> {
  if (currentUserId != null) {
    const me = await http<UserView[]>(
      `/users?id=eq.${currentUserId}&select=id,loginId,name,email,uiLanguage`,
    );
    if (me.length > 0) return me[0];
  }
  const me = await http<UserView[]>(`/users?select=id,loginId,name,email,uiLanguage&limit=1`);
  return me[0];
}

function buildAuth(): AuthPort {
  return {
    async login(data: LoginRequest): Promise<AuthResponse> {
      // 테이블: users, RLS/함수 없이 단순 조회 가정
      const q = new URLSearchParams({
        select: "id,loginId,name,email,uiLanguage",
        loginId: `eq.${data.loginId}`,
      });
      const users = await http<UserView[]>(`/users?${q.toString()}`);
      const user = users[0];
      if (!user) throw new Error("Invalid credentials");
      currentUserId = user.id;
      return {
        token: PUBLIC_KEY || "sb-token",
        user: {
          id: user.id,
          loginId: user.loginId,
          name: user.name,
          email: user.email,
          uiLanguage: user.uiLanguage,
        },
      };
    },
    async signup(data) {
      const created = await http<UserView[]>(`/users`, {
        method: "POST",
        body: JSON.stringify([data]),
      });
      const user = created[0];
      currentUserId = user.id;
      return {
        token: PUBLIC_KEY || "sb-token",
        user: {
          id: user.id,
          loginId: user.loginId,
          name: user.name,
          email: user.email,
          uiLanguage: user.uiLanguage,
        },
      };
    },
    async logout() {
      currentUserId = null;
    },
  };
}

function buildLecture(): LecturePort {
  return {
    async getLectures(): Promise<Lecture[]> {
      const qs = new URLSearchParams({ select: "*" });
      return http<Lecture[]>(`/lectures?${qs.toString()}`);
    },
    async getLecture(id: number): Promise<SessionDetailResponse> {
      const base = (await http<Lecture[]>(`/lectures?id=eq.${id}&select=*`))[0];
      const transcripts = await http<Transcript[]>(`/transcripts?lectureId=eq.${id}&select=*`);
      const summaries = await http<Summary[]>(`/summaries?lectureId=eq.${id}&select=*`);
      const qna = await http<QnA[]>(`/qna?lectureId=eq.${id}&select=*`);
      return { ...base, transcripts, summaries, qna } as SessionDetailResponse;
    },
    async createLecture(data: CreateLectureRequest): Promise<Lecture> {
      // 현재 사용자 조회하여 userId 추가
      const currentUser = await getCurrentUser();

      // Supabase PostgREST는 multipart/form-data를 지원하지 않으므로
      // 파일이 있는 경우 base64로 인코딩하여 JSON으로 전송
      if (data.files && data.files.length > 0) {
        // 파일들을 base64로 변환
        const filePromises = data.files.map((file) => {
          return new Promise<{ name: string; content: string; type: string }>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
              const base64 = (reader.result as string).split(",")[1]; // data:...;base64, 부분 제거
              resolve({
                name: file.name,
                content: base64,
                type: file.type,
              });
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
          });
        });

        const encodedFiles = await Promise.all(filePromises);
        const payload = {
          title: data.title,
          subject: data.subject,
          sttLanguage: data.sttLanguage,
          userId: currentUser.id,
          files: encodedFiles,
        };

        const created = await http<Lecture[]>(`/lectures`, {
          method: "POST",
          body: JSON.stringify([payload]),
        });
        return created[0];
      } else {
        // 파일이 없는 경우 기존 JSON 방식 사용
        const payload = { ...data, userId: currentUser.id };
        const created = await http<Lecture[]>(`/lectures`, {
          method: "POST",
          body: JSON.stringify([payload]),
        });
        return created[0];
      }
    },
    async updateLectureTitle(id: number, data: UpdateLectureTitleRequest): Promise<Lecture> {
      const updated = await http<Lecture[]>(`/lectures?id=eq.${id}`, {
        method: "PATCH",
        body: JSON.stringify({ title: data.title }),
      });
      return updated[0];
    },
    async deleteLecture(id: number): Promise<void> {
      await http<void>(`/lectures?id=eq.${id}`, { method: "DELETE" });
    },
    async endLecture(id: number, data?: UpdateLectureTitleRequest): Promise<Lecture> {
      const payload: Partial<Lecture> = { status: "completed", ...(data || {}) } as any;
      const updated = await http<Lecture[]>(`/lectures?id=eq.${id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      return updated[0];
    },
    async addBookmark(data: BookmarkRequest): Promise<Bookmark> {
      // 현재 사용자 조회하여 userId 추가
      const currentUser = await getCurrentUser();
      const payload = { ...data, userId: currentUser.id };
      const created = await http<Bookmark[]>(`/bookmarks`, {
        method: "POST",
        body: JSON.stringify([payload]),
      });
      return created[0];
    },
    async getBookmarks(lectureId: number, sectionIndex: number): Promise<Bookmark[]> {
      return http<Bookmark[]>(
        `/bookmarks?lectureId=eq.${lectureId}&sectionIndex=eq.${sectionIndex}&select=*`,
      );
    },
    async deleteBookmark(bookmarkId: number): Promise<void> {
      await http<void>(`/bookmarks?id=eq.${bookmarkId}`, { method: "DELETE" });
    },
    async getTranscripts(lectureId: number, sinceSection?: number): Promise<Transcript[]> {
      const filters = [`lectureId=eq.${lectureId}`];
      if (sinceSection != null) filters.push(`sectionIndex=gte.${sinceSection}`);
      return http<Transcript[]>(`/transcripts?${filters.join("&")}&select=*`);
    },
    async getSummaries(lectureId: number, sinceSection?: number): Promise<Summary[]> {
      const filters = [`lectureId=eq.${lectureId}`];
      if (sinceSection != null) filters.push(`sectionIndex=gte.${sinceSection}`);
      return http<Summary[]>(`/summaries?${filters.join("&")}&select=*`);
    },
    async getResources(
      lectureId: number,
      sectionIndex: number,
      type?: Resource["type"],
    ): Promise<Resource[]> {
      const filters = [`lectureId=eq.${lectureId}`, `sectionIndex=eq.${sectionIndex}`];
      if (type) filters.push(`type=eq.${type}`);
      return http<Resource[]>(`/resources?${filters.join("&")}&select=*`);
    },
    async getQnA(lectureId: number, sectionIndex: number, type?: QnA["type"]): Promise<QnA[]> {
      const filters = [`lectureId=eq.${lectureId}`, `sectionIndex=eq.${sectionIndex}`];
      if (type) filters.push(`type=eq.${type}`);
      return http<QnA[]>(`/qna?${filters.join("&")}&select=*`);
    },
    async aiCallback(payload: any): Promise<{ message: string }> {
      // 함수 호출 대신 모의 성공
      return { message: "ok" };
    },
    async generateSummary(
      lectureId: number,
      sectionIndex: number,
    ): Promise<{ success: boolean; summary?: string; sectionIndex: number; error?: string }> {
      // Supabase 백엔드는 아직 구현되지 않음
      return { success: false, sectionIndex, error: "Not implemented" };
    },
    async generateQnA(
      lectureId: number,
      sectionIndex: number,
    ): Promise<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }> {
      // Supabase 백엔드는 아직 구현되지 않음
      return { success: false, sectionIndex, error: "Not implemented" };
    },
    async generateResources(
      lectureId: number,
      sectionIndex: number,
    ): Promise<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }> {
      // Supabase 백엔드는 아직 구현되지 않음
      return { success: false, sectionIndex, error: "Not implemented" };
    },
    connectTranscription(sessionId: string | number): WebSocket {
      return new WebSocket(`${WS_BASE}/ws/transcription?sessionId=${sessionId}`);
    },
    sendAudioData(ws: WebSocket, audioData: ArrayBuffer): void {
      ws.send(audioData);
    },
  };
}

function buildSettings(): SettingsPort {
  return {
    async getUser(): Promise<UserView> {
      return getCurrentUser();
    },
    async setLanguage(data: SetLanguageRequest): Promise<UserView> {
      const me = await this.getUser();
      // data.language는 이미 코드(ko, en, ja, zh)로 전달됨
      const updated = await http<UserView[]>(`/users?id=eq.${me.id}`, {
        method: "PATCH",
        body: JSON.stringify({ uiLanguage: data.language || "ko" }),
      });
      const result = updated[0];
      return { ...result, uiLanguage: result.uiLanguage || "ko" };
    },
    async setPassword(data: SetPasswordRequest): Promise<UserView> {
      const me = await this.getUser();
      const updated = await http<UserView[]>(`/users?id=eq.${me.id}`, {
        method: "PATCH",
        body: JSON.stringify({ password: data.newPassword }),
      });
      return updated[0];
    },
  };
}

export function createSupabaseBackend(): BackendPort {
  return { auth: buildAuth(), lecture: buildLecture(), settings: buildSettings() };
}
