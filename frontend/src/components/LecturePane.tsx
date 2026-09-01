import React from "react";
import { ScrollArea } from "./ui/scroll-area";
import SectionCard from "./SectionCard";
import type { SectionData } from "./SessionTypes";

interface LecturePaneProps {
  error: string | null;
  loading: boolean;
  hasRecordingStarted: boolean;
  hasAnySectionData: boolean;
  sectionsData: SectionData[];
  transcription: string;
  onSummaryClick: (summaryKey: number, sectionIndex: number) => void;
  t: (key: string) => string;
  lectureScrollViewportRef: React.RefObject<HTMLDivElement>;
  splitMode: boolean;
}

export function LecturePane({
  error,
  loading,
  hasRecordingStarted,
  hasAnySectionData,
  sectionsData,
  transcription,
  onSummaryClick,
  t,
  lectureScrollViewportRef,
  splitMode,
}: LecturePaneProps) {
  return (
    <div
      className={`${
        !splitMode ? "w-full" : "w-1/3"
      } overflow-hidden p-6 transition-all duration-300`}
    >
      <div ref={lectureScrollViewportRef} className="h-full overflow-y-auto">
        <div className="space-y-6 safe-scroll">
          {error && (
            <div className="bg-red-50 text-red-600 border border-red-200 rounded-lg p-4 text-sm">
              {error}
            </div>
          )}
          {loading ? (
            <div className="text-center text-muted-foreground py-12">{t("session.loading")}</div>
          ) : !hasRecordingStarted ? (
            <div className="text-center text-muted-foreground py-12">
              강의 시작 버튼을 눌러 실시간 기록을 시작하세요.
            </div>
          ) : !hasAnySectionData ? (
            <div className="text-center text-muted-foreground py-12">
              {t("session.noSummaries")}
            </div>
          ) : (
            sectionsData.map((sectionData) => (
              <SectionCard
                key={sectionData.sectionKey}
                sectionIndex={sectionData.sectionIndex}
                sectionKey={sectionData.sectionKey}
                transcriptText={sectionData.transcriptText}
                liveTranscriptText={sectionData.liveTranscriptText}
                displayText={sectionData.displayText}
                summaryText={sectionData.summaryText}
                summaryKey={sectionData.summaryKey}
                isCurrentSection={sectionData.isCurrentSection}
                isSelected={sectionData.isSelected}
                isGenerating={sectionData.isGenerating}
                isClickable={sectionData.isClickable}
                transcription={transcription}
                onSummaryClick={onSummaryClick}
                t={t}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
