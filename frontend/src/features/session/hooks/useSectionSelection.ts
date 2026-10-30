import { useEffect, useEffectEvent, useState } from "react";
import type { Summary } from "../api/schemas";
import { findLatestFinalSection } from "../lib/sectionViews";

/**
 * 분할 화면에 띄울 섹션 선택을 관리한다.
 *
 * 직접 고른 섹션을 보여 주되, 오토 모드에서는 확정 요약이 있는 가장 최근 섹션을 자동으로 보여 준다.
 * 섹션이 새로 선택될 때마다 그 섹션의 추가 카드를 요청한다.
 *
 * @param summaries 저장된 요약
 * @param requestCards 섹션의 추가 카드 생성을 요청하는 함수
 * @returns 선택된 섹션(`null`이면 분할 화면 닫힘), 오토 모드 여부, 선택·닫기·오토 모드 전환 함수
 */
export function useSectionSelection(
  summaries: Summary[],
  requestCards: (sectionIndex: number) => void,
) {
  const [manualSection, setManualSection] = useState<number | null>(null);
  const [autoMode, setAutoMode] = useState(false);
  const latestFinalSection = findLatestFinalSection(summaries);
  const selectedSection = autoMode ? (latestFinalSection ?? manualSection) : manualSection;

  const requestCardsForAutoSelection = useEffectEvent((sectionIndex: number) =>
    requestCards(sectionIndex),
  );
  useEffect(() => {
    if (autoMode && latestFinalSection !== null) requestCardsForAutoSelection(latestFinalSection);
  }, [autoMode, latestFinalSection]);

  return {
    selectedSection,
    autoMode,
    // 이미 선택된 섹션을 다시 누르면 분할 화면을 닫음
    select: (sectionIndex: number) => {
      if (sectionIndex === selectedSection) {
        setManualSection(null);
        return;
      }
      setManualSection(sectionIndex);
      requestCards(sectionIndex);
    },
    close: () => {
      setManualSection(null);
      setAutoMode(false);
    },
    toggleAutoMode: () => setAutoMode((value) => !value),
  };
}
