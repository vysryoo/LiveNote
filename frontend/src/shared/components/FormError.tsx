import type { ParseKeys } from "i18next";
import { useTranslation } from "react-i18next";

const DEFAULT_CLASS_NAME = "text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2";

/**
 * 폼 제출 실패처럼 특정 입력칸에 속하지 않는 오류 메시지를 표시한다.
 *
 * @param props.messageKey 번역 키. 없으면 아무것도 그리지 않음
 * @param props.className 지정하면 기본 스타일 대신 사용
 */
export function FormError({ messageKey, className }: { messageKey?: string; className?: string }) {
  const { t } = useTranslation();
  if (!messageKey) return null;
  return <div className={className ?? DEFAULT_CLASS_NAME}>{t(messageKey as ParseKeys)}</div>;
}
