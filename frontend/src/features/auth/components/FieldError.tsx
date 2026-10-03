import type { ParseKeys } from "i18next";
import { useTranslation } from "react-i18next";

/**
 * 폼 입력칸 아래에 검사 실패 메시지를 표시한다.
 *
 * @param props.messageKey zod 스키마에 지정한 번역 키. 없으면 아무것도 그리지 않음
 */
export function FieldError({ messageKey }: { messageKey?: string }) {
  const { t } = useTranslation();
  if (!messageKey) return null;
  return <p className="text-sm text-red-600">{t(messageKey as ParseKeys)}</p>;
}
