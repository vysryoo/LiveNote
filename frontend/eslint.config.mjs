import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import prettierConfig from "eslint-config-prettier";

// eslint-plugin-react-hooks v7이 흡수한 React Compiler 안전성 규칙.
// SessionPage.tsx 등 기존 코드가 아직 위반 중이므로 Phase 4 분해 전까지는 warn으로 시작.
const reactCompilerRules = {
  "react-hooks/capitalized-calls": "warn",
  "react-hooks/static-components": "warn",
  "react-hooks/use-memo": "warn",
  "react-hooks/void-use-memo": "warn",
  "react-hooks/preserve-manual-memoization": "warn",
  "react-hooks/memo-dependencies": "warn",
  "react-hooks/incompatible-library": "warn",
  "react-hooks/immutability": "warn",
  "react-hooks/globals": "warn",
  "react-hooks/refs": "warn",
  "react-hooks/memoized-effect-dependencies": "warn",
  "react-hooks/exhaustive-effect-dependencies": "warn",
  "react-hooks/set-state-in-effect": "warn",
  "react-hooks/no-deriving-state-in-effects": "warn",
  "react-hooks/error-boundaries": "warn",
  "react-hooks/purity": "warn",
  "react-hooks/set-state-in-render": "warn",
  "react-hooks/hooks": "warn",
};

export default tseslint.config(
  {
    // components/ui는 shadcn/ui에서 그대로 가져온 벤더 코드라 린트 대상에서 제외.
    ignores: ["build/**", "node_modules/**", "src/components/ui/**"],
  },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      reactHooks.configs.flat["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    rules: {
      ...reactCompilerRules,
      "no-console": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      "react-refresh/only-export-components": "warn",
      "@typescript-eslint/ban-ts-comment": ["error", { "ts-nocheck": "allow-with-description" }],
    },
  },
  prettierConfig,
);
