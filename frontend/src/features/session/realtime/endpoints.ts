const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8080";

export const STOMP_BROKER_URL = `${WS_BASE}/ws`;

/**
 * 녹음 음성을 보내는 WebSocket 주소를 만든다.
 *
 * @param lectureId 강의 ID
 * @returns WebSocket 주소
 */
export function buildTranscriptionSocketUrl(lectureId: number): string {
  return `${WS_BASE}/ws/transcription?sessionId=${lectureId}`;
}
