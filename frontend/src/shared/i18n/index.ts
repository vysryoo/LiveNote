import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ko from "./locales/ko.json";
import en from "./locales/en.json";
import ja from "./locales/ja.json";
import zh from "./locales/zh.json";

export const resources = {
  ko: { translation: ko },
  en: { translation: en },
  ja: { translation: ja },
  zh: { translation: zh },
} as const;

export type LanguageCode = keyof typeof resources;

export const LANGUAGE_CODES = ["ko", "en", "ja", "zh"] as const satisfies readonly LanguageCode[];

/**
 * 값이 지원하는 언어 코드인지 판별한다.
 *
 * @param value 판별할 값
 * @returns 지원하는 언어 코드이면 `true`
 */
export function isLanguageCode(value: unknown): value is LanguageCode {
  return LANGUAGE_CODES.some((code) => code === value);
}

// 언어 선택 UI에서 각 언어를 자기 언어로 표기
export const LANGUAGE_LABELS: Record<LanguageCode, string> = {
  ko: "한국어",
  en: "English",
  ja: "日本語",
  zh: "汉语",
};

// 번역 리소스를 번들에 포함하므로 동기 초기화로 첫 렌더부터 번역문을 표시
void i18n.use(initReactI18next).init({
  resources,
  lng: "ko",
  fallbackLng: "ko",
  initAsync: false,
  interpolation: { escapeValue: false },
});

export default i18n;
