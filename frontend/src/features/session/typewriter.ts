// 초당 약 100자. 이전 백엔드 연출(0.1초마다 10자)과 같은 속도
export const TYPEWRITER_TICK_MS = 50;
const TYPEWRITER_CHARS_PER_TICK = 5;

/**
 * 글자가 써지는 연출에서 다음 순간에 보일 글자 수를 구한다.
 *
 * @param shown 지금 보이는 글자 수
 * @param total 전체 글자 수
 * @param charsPerTick 한 번에 늘릴 글자 수
 * @returns 다음에 보일 글자 수. 전체 글자 수를 넘지 않음
 */
export function advanceReveal(
  shown: number,
  total: number,
  charsPerTick: number = TYPEWRITER_CHARS_PER_TICK,
): number {
  return Math.min(total, shown + charsPerTick);
}
