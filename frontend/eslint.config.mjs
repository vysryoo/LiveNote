import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import prettierConfig from "eslint-config-prettier";

// eslint-plugin-react-hooks v7이 흡수한 React Compiler 안전성 규칙.
const reactCompilerRules = {
  "react-hooks/capitalized-calls": "error",
  "react-hooks/static-components": "error",
  "react-hooks/use-memo": "error",
  "react-hooks/void-use-memo": "error",
  "react-hooks/preserve-manual-memoization": "error",
  "react-hooks/memo-dependencies": "error",
  "react-hooks/incompatible-library": "error",
  "react-hooks/immutability": "error",
  "react-hooks/globals": "error",
  "react-hooks/refs": "error",
  "react-hooks/memoized-effect-dependencies": "error",
  "react-hooks/exhaustive-effect-dependencies": "error",
  "react-hooks/set-state-in-effect": "error",
  "react-hooks/no-deriving-state-in-effects": "error",
  "react-hooks/error-boundaries": "error",
  "react-hooks/purity": "error",
  "react-hooks/set-state-in-render": "error",
  "react-hooks/hooks": "error",
};

export default tseslint.config(
  {
    // shared/ui는 shadcn/ui에서 그대로 가져온 벤더 코드라 린트 대상에서 제외.
    ignores: ["build/**", "node_modules/**", "src/shared/ui/**"],
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
