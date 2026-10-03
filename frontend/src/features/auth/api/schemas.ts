import { z } from "zod";
import { LANGUAGE_CODES } from "@/shared/i18n";

// 언어 미설정 사용자나 지원하지 않는 값은 기본 언어로 취급
const uiLanguageSchema = z.enum(LANGUAGE_CODES).catch("ko");

export const userSchema = z.object({
  id: z.number(),
  loginId: z.string(),
  name: z.string(),
  email: z.string().nullable(),
  uiLanguage: uiLanguageSchema,
});

export const authResponseSchema = z.object({
  token: z.string(),
  user: userSchema,
});

export type User = z.infer<typeof userSchema>;
export type AuthResponse = z.infer<typeof authResponseSchema>;
