import { useTranslation } from "react-i18next";
import type { SectionView } from "../sectionViews";

const GRADIENT_BORDER = {
  border: "2px solid transparent",
  backgroundImage:
    "linear-gradient(white, white), linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
  backgroundOrigin: "border-box",
  backgroundClip: "padding-box, border-box",
} as const;

type SectionCardProps = {
  section: SectionView;
  onSummaryClick: (sectionIndex: number) => void;
};

export function SectionCard({ section, onSummaryClick }: SectionCardProps) {
  const { t } = useTranslation();
  const { sectionIndex, transcriptText, summaryText, isCurrent, isSelected, isClickable } = section;

  return (
    <div>
      <div className="rounded-lg p-6 bg-white mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-[16px]">{t("session.header.record")}</h4>
          {isCurrent && (
            <span className="text-xs font-semibold text-[#6A737D]">{t("session.live")}</span>
          )}
        </div>
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {transcriptText || t("session.noTranscript")}
        </p>
      </div>

      <div
        onClick={isClickable ? () => onSummaryClick(sectionIndex) : undefined}
        className={`rounded-lg p-6 transition-all relative ${
          isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-60"
        } ${
          isSelected
            ? "bg-gradient-to-br from-[#4D82E0] via-[#639BEE] to-[#83EAF1] text-white"
            : "bg-white hover:bg-muted"
        }`}
        style={
          isSelected ? undefined : summaryText ? GRADIENT_BORDER : { border: "2px solid #C3C7CB" }
        }
      >
        <div className="flex items-center justify-between mb-4">
          <h4 className={isSelected ? "text-white" : ""}>{t("session.header.summary")}</h4>
        </div>
        <p
          className={`text-sm ${isSelected ? "text-white" : "text-muted-foreground"} whitespace-pre-line`}
        >
          {summaryText || t("session.noSummaryText")}
        </p>
      </div>
    </div>
  );
}
