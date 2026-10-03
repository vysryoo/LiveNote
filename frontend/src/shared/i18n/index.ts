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

// 번역 리소스를 번들에 포함하므로 동기 초기화로 첫 렌더부터 번역문을 표시
void i18n.use(initReactI18next).init({
  resources,
  lng: "ko",
  fallbackLng: "ko",
  initAsync: false,
  interpolation: { escapeValue: false },
});

export default i18n;
