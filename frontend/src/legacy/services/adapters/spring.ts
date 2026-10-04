import type {
  BackendPort,
  Bookmark,
  BookmarkRequest,
  LecturePort,
  SessionDetailResponse,
  Summary,
  Transcript,
  QnA,
  Resource,
} from "../ports";
import { request } from "@/shared/lib/http";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8080";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  return (await request(path, init)) as T;
}

function buildLecture(): LecturePort {
  return {
    async getLecture(id: number): Promise<SessionDetailResponse> {
      return http<SessionDetailResponse>(`/lectures/${id}/detail`);
    },
    async addBookmark(data: BookmarkRequest): Promise<Bookmark> {
      const payload = {
        ...data,
        // 백엔드 Enum은 대문자(QNA/RESOURCE)만 허용
        targetType: data.targetType.toUpperCase(),
      };
      const res = await http<Bookmark>(`/bookmarks`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      return { ...res, targetType: res.targetType.toLowerCase() as Bookmark["targetType"] };
    },
    async getBookmarks(lectureId: number, sectionIndex: number): Promise<Bookmark[]> {
      const res = await http<Bookmark[]>(
        `/bookmarks?lectureId=${lectureId}&sectionIndex=${sectionIndex}`,
      );
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
    async getResources(
      lectureId: number,
      sectionIndex: number,
      type?: Resource["type"],
    ): Promise<Resource[]> {
      const qs = new URLSearchParams({
        lectureId: String(lectureId),
        sectionIndex: String(sectionIndex),
      });
      if (type) qs.append("type", type);
      return http<Resource[]>(`/resources?${qs.toString()}`);
    },
    async getQnA(lectureId: number, sectionIndex: number, type?: QnA["type"]): Promise<QnA[]> {
      const qs = new URLSearchParams({
        lectureId: String(lectureId),
        sectionIndex: String(sectionIndex),
      });
      if (type) qs.append("type", type);
      return http<QnA[]>(`/qna?${qs.toString()}`);
    },
    async aiCallback(payload: any): Promise<{ message: string }> {
      return http<{ message: string }>(`/ai/callback`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    async generateSummary(
      lectureId: number,
      sectionIndex: number,
      phase?: "partial" | "final",
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
        { method: "POST" },
      );
    },
    async generateQnA(
      lectureId: number,
      sectionIndex: number,
    ): Promise<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }> {
      return http<{ success: boolean; qna?: any[]; sectionIndex: number; error?: string }>(
        `/ai/generate-qna?lectureId=${lectureId}&sectionIndex=${sectionIndex}`,
        { method: "POST" },
      );
    },
    async generateResources(
      lectureId: number,
      sectionIndex: number,
    ): Promise<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }> {
      return http<{ success: boolean; resources?: any[]; sectionIndex: number; error?: string }>(
        `/ai/generate-resources?lectureId=${lectureId}&sectionIndex=${sectionIndex}`,
        { method: "POST" },
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
      sectionIndex: number,
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
      return http(`/cards-status?lectureId=${lectureId}&sectionIndex=${sectionIndex}`);
    },
    async startQnAStream(
      lectureId: number,
      sectionIndex: number,
      cardIndex: number,
      qnaType?: string,
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
      resourceType?: string,
    ): Promise<{ success: boolean; cardId: string; type: string }> {
      const url = resourceType
        ? `/start-resources-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}&resourceType=${encodeURIComponent(resourceType)}`
        : `/start-resources-stream?lectureId=${lectureId}&sectionIndex=${sectionIndex}&cardIndex=${cardIndex}`;
      return http<{ success: boolean; cardId: string; type: string }>(url, { method: "POST" });
    },
  };
}

export function createSpringBackend(): BackendPort {
  return { lecture: buildLecture() };
}
