import type { ParseKeys } from "i18next";
import { HttpError } from "@/shared/lib/http";

// 백엔드 UserService가 예외 메시지로 보내는 영문 코드
const SERVER_MESSAGE_KEYS: Record<string, ParseKeys> = {
  // 존재하지 않는 아이디도 같은 문구로 안내해 아이디 존재 여부를 드러내지 않음
  "no user": "auth.errors.badCredential",
  "bad credential": "auth.errors.badCredential",
  "duplicated loginId": "auth.errors.duplicatedLoginId",
  "duplicated email": "auth.errors.duplicatedEmail",
  "invalid current password": "auth.errors.invalidCurrentPassword",
};

/**
 * 인증 요청 실패를 화면에 표시할 번역 키로 변환한다.
 *
 * @param error 요청 중 발생한 에러
 * @returns 번역 키. 알려진 서버 메시지가 아니면 일반 실패 문구의 키
 */
export function toAuthErrorKey(error: unknown): ParseKeys {
  if (error instanceof HttpError) {
    return SERVER_MESSAGE_KEYS[error.message] ?? "common.requestFailed";
  }
  return "common.requestFailed";
}
