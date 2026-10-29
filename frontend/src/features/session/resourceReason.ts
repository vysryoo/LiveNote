// AI 서버가 검증 없이 추천했거나 검증에 실패했을 때 reason에 넣는 자리 표시 값
const PLACEHOLDER_REASONS = new Set([
  "search",
  "heuristic",
  "검증 완료",
  "llm evaluation",
  "llm verification",
  "scoring failed",
  "parsing failed",
  "aligned with key terms (stub).",
]);
const PLACEHOLDER_PREFIXES = ["검증 실패"];

/**
 * 자료 카드에 보여 줄 추천 이유를 고른다.
 *
 * @param reason 백엔드가 준 추천 이유. 없을 수 있음
 * @returns 화면에 보여 줄 추천 이유. 비어 있거나 자리 표시 값이면 null
 */
export function toDisplayReason(reason: string | null | undefined): string | null {
  const trimmed = reason?.trim();
  if (!trimmed) return null;
  if (PLACEHOLDER_REASONS.has(trimmed.toLowerCase())) return null;
  if (PLACEHOLDER_PREFIXES.some((prefix) => trimmed.startsWith(prefix))) return null;
  return trimmed;
}
