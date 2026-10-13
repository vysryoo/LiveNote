import { getAuthToken } from "@/shared/lib/authToken";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8080";

export const STOMP_BROKER_URL = `${WS_BASE}/ws`;

/**
 * 녹음 음성을 보내는 WebSocket 주소를 만든다.
 *
 * 브라우저 WebSocket은 헤더를 붙일 수 없어 로그인 토큰을 쿼리로 전달한다.
 *
 * @param lectureId 강의 ID
 * @returns WebSocket 주소
 */
export function buildTranscriptionSocketUrl(lectureId: number): string {
  const params = new URLSearchParams({ sessionId: String(lectureId) });
  const token = getAuthToken();
  if (token) params.set("token", token);
  return `${WS_BASE}/ws/transcription?${params.toString()}`;
}
