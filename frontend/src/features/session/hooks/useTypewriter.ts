import { useEffect, useState } from "react";
import { advanceReveal, TYPEWRITER_TICK_MS } from "../typewriter";

/**
 * 텍스트가 한 글자씩 써지듯 나타나게 한다. 서버와 무관한 화면 연출이다.
 *
 * @param text 보여 줄 전체 텍스트
 * @param animate 연출 여부. `false`면 처음부터 전체를 보여 줌
 * @returns 지금 보여 줄 텍스트
 */
export function useTypewriter(text: string, animate: boolean): string {
  const [shown, setShown] = useState(animate ? 0 : text.length);
  const isDone = shown >= text.length;

  useEffect(() => {
    if (!animate || isDone) return;
    const timer = setInterval(
      () => setShown((current) => advanceReveal(current, text.length)),
      TYPEWRITER_TICK_MS,
    );
    return () => clearInterval(timer);
  }, [animate, isDone, text.length]);

  return animate ? text.slice(0, shown) : text;
}
