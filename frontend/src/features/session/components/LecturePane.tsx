import type { RefObject } from "react";
import { useTranslation } from "react-i18next";
import type { SectionView } from "../sectionViews";
import { SectionCard } from "./SectionCard";

type LecturePaneProps = {
  status: "loading" | "error" | "notStarted" | "ready";
  sections: SectionView[];
  isSplit: boolean;
  scrollViewportRef: RefObject<HTMLDivElement | null>;
  onSummaryClick: (sectionIndex: number) => void;
};

export function LecturePane({
  status,
  sections,
  isSplit,
  scrollViewportRef,
  onSummaryClick,
}: LecturePaneProps) {
  const { t } = useTranslation();
  const message =
    status === "loading"
      ? t("session.loading")
      : status === "notStarted"
        ? t("session.startHint")
        : status === "ready" && sections.length === 0
          ? t("session.noSummaries")
          : null;

  return (
    <div
      className={`${isSplit ? "w-1/3" : "w-full"} overflow-hidden p-6 transition-all duration-300`}
    >
      <div ref={scrollViewportRef} className="h-full overflow-y-auto">
        <div className="space-y-6 safe-scroll">
          {status === "error" && (
            <div className="bg-red-50 text-red-600 border border-red-200 rounded-lg p-4 text-sm">
              {t("session.fetchError")}
            </div>
          )}
          {message ? (
            <div className="text-center text-muted-foreground py-12">{message}</div>
          ) : (
            sections.map((section) => (
              <SectionCard
                key={section.sectionIndex}
                section={section}
                onSummaryClick={onSummaryClick}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
