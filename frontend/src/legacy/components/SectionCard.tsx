import React, { memo } from "react";
import { AnimatedLoaderIcon } from "./AnimatedLoaderIcon";

interface SectionCardProps {
  sectionIndex: number;
  sectionKey: string;
  transcriptText: string;
  liveTranscriptText: string;
  displayText: string;
  summaryText: string;
  summaryKey: number;
  isCurrentSection: boolean;
  isSelected: boolean;
  isGenerating: boolean;
  isClickable: boolean;
  transcription: string; // currentSection일 때만 사용
  onSummaryClick: (summaryKey: number, sectionIndex: number) => void;
  t: (key: string) => string;
}

// 섹션 카드 컴포넌트 (메모이제이션으로 리렌더링 최소화)
const SectionCard = memo(
  ({
    sectionIndex,
    sectionKey,
    transcriptText,
    liveTranscriptText,
    displayText,
    summaryText,
    summaryKey,
    isCurrentSection,
    isSelected,
    isGenerating,
    isClickable,
    transcription,
    onSummaryClick,
    t,
  }: SectionCardProps) => {
    const hasNoSummary = summaryText === t("session.noSummaryText");

    // currentSection일 때만 transcription 사용
    const finalDisplayText =
      !displayText && isCurrentSection ? transcription : displayText || t("session.noTranscript");

    return (
      <div key={sectionKey}>
        {/* 강의 기록 컴포넌트 */}
        <div className="rounded-lg p-6 bg-white mb-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-[16px]">{t("session.header.record")}</h4>
            {isCurrentSection && (
              <span className="text-xs font-semibold text-[#6A737D]">실시간</span>
            )}
          </div>
          <p className="text-sm text-muted-foreground whitespace-pre-line">{finalDisplayText}</p>
        </div>

        {/* 실시간 요약 컴포넌트 */}
        <div
          onClick={isClickable ? () => onSummaryClick(summaryKey, sectionIndex) : undefined}
          className={`rounded-lg p-6 transition-all relative ${
            isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-60"
          } ${
            isSelected
              ? "bg-gradient-to-br from-[#4D82E0] via-[#639BEE] to-[#83EAF1] text-white"
              : "bg-white hover:bg-muted"
          }`}
          style={
            !isSelected
              ? hasNoSummary
                ? {
                    border: "2px solid #C3C7CB",
                  }
                : isGenerating
                  ? {
                      border: "2px solid transparent",
                      backgroundImage:
                        "linear-gradient(white, white), linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                      backgroundOrigin: "border-box",
                      backgroundClip: "padding-box, border-box",
                    }
                  : {
                      border: "2px solid transparent",
                      backgroundImage:
                        "linear-gradient(white, white), linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                      backgroundOrigin: "border-box",
                      backgroundClip: "padding-box, border-box",
                    }
              : undefined
          }
        >
          <div className="flex items-center justify-between mb-4">
            <h4 className={isSelected ? "text-white" : ""}>{t("session.header.summary")}</h4>
          </div>
          {isGenerating ? (
            <div className="flex items-center gap-2">
              <AnimatedLoaderIcon id={`grad-summary-${sectionIndex}`} />
              <p className={`text-sm ${isSelected ? "text-white" : "text-muted-foreground"}`}>
                {summaryText}
              </p>
            </div>
          ) : (
            <p
              className={`text-sm ${
                isSelected ? "text-white" : "text-muted-foreground"
              } whitespace-pre-line`}
            >
              {summaryText}
            </p>
          )}
        </div>
      </div>
    );
  },
  (prevProps, nextProps) => {
    // 커스텀 비교 함수: 필요한 props만 비교
    return (
      prevProps.sectionIndex === nextProps.sectionIndex &&
      prevProps.sectionKey === nextProps.sectionKey &&
      prevProps.transcriptText === nextProps.transcriptText &&
      prevProps.liveTranscriptText === nextProps.liveTranscriptText &&
      prevProps.displayText === nextProps.displayText &&
      prevProps.summaryText === nextProps.summaryText &&
      prevProps.summaryKey === nextProps.summaryKey &&
      prevProps.isCurrentSection === nextProps.isCurrentSection &&
      prevProps.isSelected === nextProps.isSelected &&
      prevProps.isGenerating === nextProps.isGenerating &&
      prevProps.isClickable === nextProps.isClickable &&
      // currentSection이 아닌 경우 transcription 비교 생략
      (!nextProps.isCurrentSection || prevProps.transcription === nextProps.transcription)
    );
  },
);

SectionCard.displayName = "SectionCard";

export default SectionCard;
