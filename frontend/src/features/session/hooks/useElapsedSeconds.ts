import { useEffect, useLayoutEffect, useRef, useState } from "react";

/**
 * 녹음 경과 시간(초)을 센다.
 *
 * 서버는 전사를 저장할 때만 시간을 알려 주므로, 화면 시계는 1초마다 직접 세고 서버 값보다 뒤처지면 서버 값으로 맞춘다.
 *
 * @param isRunning 시계를 진행할지 여부. 녹음 중이고 마이크 입력이 있을 때만 `true`
 * @param serverSeconds 서버 기준으로 확인된 경과 시간(초)
 * @returns 표시할 경과 시간(초)
 */
export function useElapsedSeconds(isRunning: boolean, serverSeconds: number): number {
  const [countedSeconds, setCountedSeconds] = useState(0);
  const serverSecondsRef = useRef(serverSeconds);

  useLayoutEffect(() => {
    serverSecondsRef.current = serverSeconds;
  });

  useEffect(() => {
    if (!isRunning) return;
    const timer = setInterval(() => {
      setCountedSeconds((prev) => Math.max(prev, serverSecondsRef.current) + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [isRunning]);

  return Math.max(countedSeconds, serverSeconds);
}
