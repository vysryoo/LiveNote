import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useMe } from "./useMe";

/**
 * 화면 언어를 로그인한 사용자의 `uiLanguage`에 맞춘다. 비로그인 상태는 한국어로 표시한다.
 */
export function useSyncUiLanguage() {
  const { data: user, isPending } = useMe();
  const { i18n } = useTranslation();
  const language = user?.uiLanguage ?? "ko";

  useEffect(() => {
    if (isPending) return;
    void i18n.changeLanguage(language);
  }, [i18n, isPending, language]);
}
