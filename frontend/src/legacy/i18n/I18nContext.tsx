import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { ParseKeys } from "i18next";
import type { LanguageCode } from "@/shared/i18n";

export type SupportedLanguage = "한국어" | "English" | "日本語" | "汉语";

// 언어 표시명과 DB 코드 간 변환 함수
export function languageToCode(lang: SupportedLanguage): LanguageCode {
  const map: Record<SupportedLanguage, LanguageCode> = {
    한국어: "ko",
    English: "en",
    日本語: "ja",
    汉语: "zh",
  };
  return map[lang] || "ko";
}

export function codeToLanguage(code: string): SupportedLanguage {
  const map: Record<string, SupportedLanguage> = {
    ko: "한국어",
    en: "English",
    ja: "日本語",
    zh: "汉语",
  };
  return map[code] || "한국어";
}

type I18nContextValue = {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string) => string;
};

// 기존 컴포넌트의 호출 형태를 유지한 채 i18next로 위임하는 어댑터
export function useI18n(): I18nContextValue {
  const { t, i18n } = useTranslation();

  const setLanguage = useCallback(
    (lang: SupportedLanguage) => {
      void i18n.changeLanguage(languageToCode(lang));
    },
    [i18n],
  );

  const translate = useCallback((key: string) => t(key as ParseKeys), [t]);

  return useMemo(
    () => ({ language: codeToLanguage(i18n.language), setLanguage, t: translate }),
    [i18n.language, setLanguage, translate],
  );
}
