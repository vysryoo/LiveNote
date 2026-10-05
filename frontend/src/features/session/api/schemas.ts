import { z } from "zod";
import { lectureSchema } from "@/features/lectures/api/schemas";

// 과거 AI 응답이 문자열 배열로 저장된 경우가 있어 한 문장으로 합침
const textSchema = z
  .union([z.string(), z.array(z.string())])
  .nullish()
  .transform((value) => (Array.isArray(value) ? value.join(" ") : (value ?? "")));

// DB 응답은 대문자, 실시간 메시지는 소문자로 와서 소문자로 통일
const lowercaseSchema = z.string().transform((value) => value.toLowerCase());

export const transcriptSchema = z.object({
  id: z.number().optional(),
  sectionIndex: z.number(),
  startSec: z.number().nullish(),
  endSec: z.number().nullish(),
  text: textSchema,
});

export const summarySchema = z.object({
  id: z.number().nullish(),
  sectionIndex: z.number(),
  startSec: z.number().nullish(),
  endSec: z.number().nullish(),
  text: textSchema,
  phase: lowercaseSchema.pipe(z.enum(["partial", "final"])).nullish(),
});

export const qnaSchema = z.object({
  id: z.number(),
  sectionIndex: z.number(),
  summaryId: z.number().nullish(),
  type: lowercaseSchema,
  question: textSchema,
  answer: textSchema,
});

export const resourceSchema = z.object({
  id: z.number(),
  sectionIndex: z.number(),
  summaryId: z.number().nullish(),
  type: lowercaseSchema,
  title: textSchema,
  text: textSchema,
  url: z.string().nullish(),
  thumbnail: z.string().nullish(),
  score: z.number().nullish(),
  reason: z.string().nullish(),
});

export const bookmarkSchema = z.object({
  id: z.number(),
  sectionIndex: z.number(),
  targetType: lowercaseSchema.pipe(z.enum(["qna", "resource"])),
  targetId: z.number(),
});

export const sessionDetailSchema = lectureSchema.extend({
  transcripts: z
    .array(transcriptSchema)
    .nullish()
    .transform((items) => items ?? []),
  summaries: z
    .array(summarySchema)
    .nullish()
    .transform((items) => items ?? []),
  resources: z
    .array(resourceSchema)
    .nullish()
    .transform((items) => items ?? []),
  qna: z
    .array(qnaSchema)
    .nullish()
    .transform((items) => items ?? []),
  bookmarks: z
    .array(bookmarkSchema)
    .nullish()
    .transform((items) => items ?? []),
});

export type Transcript = z.infer<typeof transcriptSchema>;
export type Summary = z.infer<typeof summarySchema>;
export type QnA = z.infer<typeof qnaSchema>;
export type Resource = z.infer<typeof resourceSchema>;
export type Bookmark = z.infer<typeof bookmarkSchema>;
export type SessionDetail = z.infer<typeof sessionDetailSchema>;
