import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { ParseKeys } from "i18next";

type I18nContextValue = {
  t: (key: string) => string;
};

// 기존 컴포넌트의 호출 형태를 유지한 채 i18next로 위임하는 어댑터
export function useI18n(): I18nContextValue {
  const { t } = useTranslation();

  const translate = useCallback((key: string) => t(key as ParseKeys), [t]);

  return useMemo(() => ({ t: translate }), [translate]);
}
