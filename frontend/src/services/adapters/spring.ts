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

const API_BASE = import.meta.env.VITE_API_URL || "/api";
const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8080";

function authHeader(): Record<string, string> {
  // Prefer in-memory token, fall back to persisted token so page reloads keep the session.
  const tokenInWindow = (window as any).SPRING_TOKEN as string | undefined;
  const tokenInStorage = typeof localStorage !== 'undefined' ? localStorage.getItem('SPRING_TOKEN') : null;
  const token = tokenInWindow || tokenInStorage || undefined;
  // Guard against literal strings 'undefined' or 'null' which can appear when code sets them accidentally
  if (!token || token === 'undefined' || token === 'null') {
    return {};
  }
  return { Authorization: `Bearer ${token}` };
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData를 사용하는 경우 Content-Type을 설정하지 않음 (브라우저가 자동으로 boundary 설정)
  const isFormData = init?.body instanceof FormData;
  const base = new Headers();
  
  if (!isFormData) {
    base.set("Content-Type", "application/json");
    const auth = authHeader();
    Object.entries(auth).forEach(([key, value]) => base.set(key, value));
  } else {
    // FormData인 경우에도 인증 헤더는 필요
    const auth = authHeader();
    Object.entries(auth).forEach(([key, value]) => base.set(key, value));
  }
  
  if (init?.headers) {
    const extra = new Headers(init.headers as HeadersInit);
    extra.forEach((value, key) => base.set(key, value));
  }
  
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers: base });
  if (!res.ok) {
    // 에러 응답을 JSON으로 파싱 시도
    let errorMessage = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errorData = await res.json();
      // 백엔드에서 {message: "..."} 형태로 반환하는 경우
      if (errorData.message) {
        errorMessage = errorData.message;
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
    } catch {
      // JSON 파싱 실패 시 텍스트로 시도
      const text = await res.text().catch(() => "");
      if (text) {
        errorMessage = text;
      }
    }
    throw new Error(errorMessage);
  }
  if (res.status === 204) return undefined as unknown as T;
  // Some backend responses are wrapped in { ok: boolean, data: T, message: string }
  const parsed = await res.json().catch(() => null);
  if (parsed && typeof parsed === "object" && Object.prototype.hasOwnProperty.call(parsed, "ok") && Object.prototype.hasOwnProperty.call(parsed, "data")) {
    if (parsed.ok) {
      return parsed.data as T;
    }
    // backend reported failure
    const msg = parsed.message || `Request failed`;
    throw new Error(msg);
  }
  return parsed as T;
}

function buildAuth(): AuthPort {
  return {
    async login(data: LoginRequest): Promise<AuthResponse> {
      const resp = await http<AuthResponse>(`/auth/login`, { method: "POST", body: JSON.stringify(data) });
      (window as any).SPRING_TOKEN = resp.token;
      try {
        localStorage.setItem('SPRING_TOKEN', resp.token);
      } catch (e) {
        // ignore storage errors in environments without localStorage
      }
      return resp;
    },
    async signup(data) {
      return http<AuthResponse>(`/auth/signup`, { method: "POST", body: JSON.stringify(data) });
    },
    async logout() {
      (window as any).SPRING_TOKEN = undefined;
      try {
        localStorage.removeItem('SPRING_TOKEN');
      } catch (e) {
        // ignore
      }
    },
  };
}

function buildLecture(): LecturePort {
  return {
    async getLectures(): Promise<Lecture[]> {
      return http<Lecture[]>(`/lectures`);
    },
    async getLecture(id: number): Promise<SessionDetailResponse> {
      return http<SessionDetailResponse>(`/lectures/${id}/detail`);
    },
    async createLecture(data: CreateLectureRequest): Promise<Lecture> {
      // 파일이 있는 경우 FormData 사용
      if (data.files && data.files.length > 0) {
        const formData = new FormData();
        formData.append("title", data.title);
        formData.append("subject", data.subject);
        formData.append("sttLanguage", data.sttLanguage);
        
        // 파일들을 FormData에 추가
        data.files.forEach((file) => {
          formData.append("files", file);
        });
        
        return http<Lecture>(`/lectures`, { 
          method: "POST", 
          body: formData 
        });
      } else {
        // 파일이 없는 경우 기존 JSON 방식 사용 (files 필드 제거)
        const { files, ...jsonData } = data;
        return http<Lecture>(`/lectures`, { 
          method: "POST", 
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(jsonData) 
        });
      }
    },
    async updateLectureTitle(id: number, data: UpdateLectureTitleRequest): Promise<Lecture> {
      return http<Lecture>(`/lectures/${id}/title`, { method: "PATCH", body: JSON.stringify(data) });
    },
    async deleteLecture(id: number): Promise<void> {
      await http<void>(`/lectures/${id}`, { method: "DELETE" });
    },
    async endLecture(id: number, data?: UpdateLectureTitleRequest): Promise<Lecture> {
      return http<Lecture>(`/lectures/${id}/end`, { method: "POST", body: JSON.stringify(data || {}) });
    },
    async addBookmark(data: BookmarkRequest): Promise<Bookmark> {
      const payload = {
        ...data,
        // 백엔드 Enum은 대문자(QNA/RESOURCE)만 허용
        targetType: data.targetType.toUpperCase(),
      };
      const res = await http<Bookmark>(`/bookmarks`, { method: "POST", body: JSON.stringify(payload) });
      return { ...res, targetType: res.targetType.toLowerCase() as Bookmark["targetType"] };
    },
    async getBookmarks(lectureId: number, sectionIndex: number): Promise<Bookmark[]> {
      const res = await http<Bookmark[]>(`/bookmarks?lectureId=${lectureId}&sectionIndex=${sectionIndex}`);
      return res.map((item) => ({
        ...item,
        // 서버 응답이 대문자일 경우 프런트 타입(소문자)로 정규화
        targetType: item.targetType.toLowerCase() as Bookmark["targetType"],
      }));
    },
    async deleteBookmark(bookmarkId: number): Promise<void> {
      await http<void>(`/bookmarks/${bookmarkId}`, { method: "DELETE" });
    },
    async getTranscripts(lectureId: number, sinceSection?: number): Promise<Transcript[]> {
      const qs = new URLSearchParams({ lectureId: String(lectureId) });
      if (sinceSection != null) qs.append("sinceSection", String(sinceSection));
      return http<Transcript[]>(`/transcripts?${qs.toString()}`);
    },
    async getSummaries(lectureId: number, sinceSection?: number): Promise<Summary[]> {
      const qs = new URLSearchParams({ lectureId: String(lectureId) });
      if (sinceSection != null) qs.append("sinceSection", String(sinceSection));
      return http<Summary[]>(`/summaries?${qs.toString()}`);
    },
    async getResources(lectureId: number, sectionIndex: number, type?: Resource["type"]): Promise<Resource[]> {
      const qs = new URLSearchParams({ lectureId: String(lectureId), sectionIndex: String(sectionIndex) });
      if (type) qs.append("type", type);
      return http<Resource[]>(`/resources?${qs.toString()}`);
    },
    async getQnA(lectureId: number, sectionIndex: number, type?: QnA["type"]): Promise<QnA[]> {
      const qs = new URLSearchParams({ lectureId: String(lectureId), sectionIndex: String(sectionIndex) });
      if (type) qs.append("type", type);
      return http<QnA[]>(`/qna?${qs.toString()}`);
    },
    async aiCallback(payload: any): Promise<{ message: string }> {
      return http<{ message: string }>(`/ai/callback`, { method: "POST", body: JSON.stringify(payload) });
    },
    async generateSummary(
      lectureId: number,
      sectionIndex: number,
      phase?: 'partial' | 'final'
    ): Promise<{ success: boolean; summary?: Summary; sectionIndex: number; error?: string }> {
      const qs = new URLSearchParams({
        lectureId: String(lectureId),
        sectionIndex: String(sectionIndex),
      });
      if (phase) {
        qs.append("phase", phase);
      }
      return http<{ success: boolean; summary?: Summary; sectionIndex: number; error?: string }>(
        `/ai/generate-summary?${qs.toString()}`,
        { method: "POST" }
      );
    },
    async generateQnA(lectureId: number, sectionIndex: number): Promise<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }> {
      return http<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }>(
        `/ai/generate-qna?lectureId=${lectureId}&sectionIndex=${sectionIndex}`,
        { method: "POST" }
      );
    },
    async generateResources(lectureId: number, sectionIndex: number): Promise<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }> {
      return http<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }>(
        `/ai/generate-resources?lectureId=${lectureId}&sectionIndex=${sectionIndex}`,
        { method: "POST" }
      );
    },
    connectTranscription(sessionId: string | number): WebSocket {
      return new WebSocket(`${WS_BASE}/ws/transcription?sessionId=${sessionId}`);
    },
    sendAudioData(ws: WebSocket, audioData: ArrayBuffer): void {
      ws.send(audioData);
    },
    async getCardsStatus(
      lectureId: number,
      sectionIndex: number
    ): Promise<{
      qnaCards: Array<{
        cardId: string;
        cardIndex: number;
        type: string;
        isComplete: boolean;
        needsStreaming?: boolean;
        data?: QnA | Resource;
      }>;
      resourceCards: Array<{
        cardId: string;
        cardIndex: number;
        type: string;
        isComplete: boolean;
        needsStreaming?: boolean;
        data?: QnA | Resource;
      }>;
    }> {
      return http(
        `/cards-status?lectureId=${lectureId}&sectionIndex=${sectionIndex}`
      );
    },
    async startQnAStream(
      lectureId: number,
      sectionIndex: number,
      cardIndex: number,
      qnaType?: string
    ): Promise<{ success: boolean; cardId: string; type: string }> {
      const url = qnaType
        ? `/start-qna-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}&qnaType=${encodeURIComponent(qnaType)}`
        : `/start-qna-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}`;
      return http<{ success: boolean; cardId: string; type: string }>(url, { method: "POST" });
    },
    async startResourceStream(
      lectureId: number,
      sectionIndex: number,
      cardIndex: number,
      resourceType?: string
    ): Promise<{ success: boolean; cardId: string; type: string }> {
      const url = resourceType
        ? `/start-resources-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}&resourceType=${encodeURIComponent(resourceType)}`
        : `/start-resources-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}`;
      return http<{ success: boolean; cardId: string; type: string }>(url, { method: "POST" });
    },
  };
}

function buildSettings(): SettingsPort {
  return {
    async getUser(): Promise<UserView> {
      return http<UserView>(`/users/me`);
    },
    async setLanguage(data: SetLanguageRequest): Promise<UserView> {
      return http<UserView>(`/users/me/language`, { method: "PATCH", body: JSON.stringify(data) });
    },
    async setPassword(data: SetPasswordRequest): Promise<UserView> {
      return http<UserView>(`/users/me/password`, { method: "PATCH", body: JSON.stringify(data) });
    },
  };
}

export function createSpringBackend(): BackendPort {
  return { auth: buildAuth(), lecture: buildLecture(), settings: buildSettings() };
}
