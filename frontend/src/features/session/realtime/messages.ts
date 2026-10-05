import { z } from "zod";
import { qnaSchema, resourceSchema, summarySchema } from "../api/schemas";

const CARD_ID_PATTERN = /^[a-z]+_(\d+)_(\d+)_(\d+)$/;

/**
 * 스트리밍 카드 ID에서 섹션 번호와 카드 번호를 꺼낸다.
 *
 * 백엔드는 `{접두사}_{강의ID}_{섹션}_{카드}` 형식으로 만들며, 접두사는 코드 경로마다 `qna`, `res`, `resource`로 다르다.
 *
 * @param cardId 스트리밍 카드 ID
 * @returns 섹션 번호와 카드 번호. 형식이 다르면 `null`
 */
export function parseCardId(cardId: string): { sectionIndex: number; cardIndex: number } | null {
  const match = CARD_ID_PATTERN.exec(cardId);
  if (!match) return null;
  return { sectionIndex: Number(match[2]), cardIndex: Number(match[3]) };
}

const cardIdSchema = z.string().transform((cardId, ctx) => {
  const parsed = parseCardId(cardId);
  if (!parsed) {
    ctx.addIssue({ code: "custom", message: `알 수 없는 카드 ID 형식: ${cardId}` });
    return z.NEVER;
  }
  return { cardId, ...parsed };
});

// 카드 ID 접두사 대신 메시지 type으로 카드 종류를 판단
const streamKindSchema = z
  .enum(["qna_stream", "resource_stream"])
  .transform((type) => (type === "qna_stream" ? "qna" : "resource"));

export const summaryMessageSchema = summarySchema.pick({
  sectionIndex: true,
  text: true,
  phase: true,
});

export const qnaListMessageSchema = z.object({
  sectionIndex: z.number(),
  items: z.array(qnaSchema),
});

export const resourceListMessageSchema = z.object({
  sectionIndex: z.number(),
  items: z.array(resourceSchema),
});

export const sectionMessageSchema = z.object({
  sectionIndex: z.number(),
});

export const transcriptMessageSchema = z.object({
  sectionIndex: z.number(),
  startSec: z.number().nullish(),
  endSec: z.number().nullish(),
  text: z.string(),
});

const streamTokenMessageSchema = z.object({
  type: streamKindSchema,
  card: cardIdSchema,
  isComplete: z.literal(false),
  token: z.string(),
  title: z.string().nullish(),
  resourceType: z.string().nullish(),
});

const streamCompleteMessageSchema = z.object({
  type: streamKindSchema,
  card: cardIdSchema,
  isComplete: z.literal(true),
  // 자료 완료 데이터에는 sectionIndex가 없어 카드 ID 값으로 채움
  data: z.record(z.string(), z.unknown()),
});

export const streamMessageSchema = z.preprocess(
  // 백엔드 필드명 cardId를 파싱 결과를 담는 card로 옮김
  (raw) => (raw && typeof raw === "object" && "cardId" in raw ? { ...raw, card: raw.cardId } : raw),
  z.discriminatedUnion("isComplete", [streamTokenMessageSchema, streamCompleteMessageSchema]),
);

export const errorMessageSchema = z.object({
  message: z.string().nullish(),
});

// 오디오 WebSocket(/ws/transcription)으로 오는 메시지. 섹션 번호가 없어 수신 측이 현재 섹션으로 지정
export const audioSocketMessageSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("transcript"),
    data: z.object({ content: z.string(), isFinal: z.boolean().default(false) }),
  }),
  z.object({
    type: z.literal("error"),
    data: z.object({ error: z.string().nullish() }),
  }),
]);

export type SummaryMessage = z.infer<typeof summaryMessageSchema>;
export type QnaListMessage = z.infer<typeof qnaListMessageSchema>;
export type ResourceListMessage = z.infer<typeof resourceListMessageSchema>;
export type SectionMessage = z.infer<typeof sectionMessageSchema>;
export type TranscriptMessage = z.infer<typeof transcriptMessageSchema>;
export type StreamMessage = z.infer<typeof streamMessageSchema>;
