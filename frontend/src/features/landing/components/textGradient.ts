import type { CSSProperties } from "react";

/**
 * 글자에 그라데이션을 입히는 인라인 style을 만든다.
 *
 * `background` 단축 속성은 `background-clip`을 초기값으로 되돌리므로 클립 속성과 함께 인라인으로 지정한다.
 *
 * @param background 글자에 입힐 배경 (예: `linear-gradient(...)`)
 * @returns 인라인 style
 */
export function textGradientStyle(background: string): CSSProperties {
  return {
    background,
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  };
}
