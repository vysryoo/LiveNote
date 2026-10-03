import "i18next";
import type ko from "./locales/ko.json";

declare module "i18next" {
  interface CustomTypeOptions {
    resources: { translation: typeof ko };
  }
}
