import { z } from "zod";

export const lectureSchema = z.object({
  id: z.number(),
  userId: z.number(),
  title: z.string().nullable(),
  // 백엔드 필드명은 subject지만 화면에서는 분야(카테고리)로 표시
  subject: z.string().nullable(),
  sttLanguage: z.string().nullable(),
  status: z.enum(["RECORDING", "COMPLETED"]),
  // 백엔드 LocalDateTime이라 시간대 없는 ISO 문자열로 옴
  createdAt: z.string(),
  endAt: z.string().nullable(),
});

export type Lecture = z.infer<typeof lectureSchema>;
