const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8080";

export const STOMP_BROKER_URL = `${WS_BASE}/ws`;

/**
 * 녹음 음성을 보내는 WebSocket 주소를 만든다.
 *
 * 브라우저 WebSocket은 헤더를 붙일 수 없어 로그인 토큰을 쿼리로 전달한다.
 *
 * @param lectureId 강의 ID
 * @param token 로그인 토큰. 서버는 연결할 때만 확인하므로 만료가 임박하지 않은 토큰을 넘김
 * @returns WebSocket 주소
 */
export function buildTranscriptionSocketUrl(lectureId: number, token: string | null): string {
  const params = new URLSearchParams({ sessionId: String(lectureId) });
  if (token) params.set("token", token);
  return `${WS_BASE}/ws/transcription?${params.toString()}`;
}
