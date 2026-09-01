import { useCallback, useMemo, useState } from "react";
import type { Summary, Transcript } from "../services/ports";
import type { SectionData } from "../components/SessionTypes";

interface UseSectionsLayoutParams {
  transcripts: Transcript[];
  summaries: Summary[];
  liveSectionTranscripts: Record<number, string>;
  isRecording: boolean;
  elapsedTime: number;
  selectedSummaryId: number | null;
  autoMode: boolean;
  transcription: string;
  currentSectionIndex?: number;
  getSectionKey: (sectionIndex: number) => string;
  formatText: (value: string | string[] | undefined) => string;
  t: (key: string) => string;
}

interface UseSectionsLayoutResult {
  sectionOrder: number[];
  sectionsData: SectionData[];
  hasAnySectionData: boolean;
  updateSectionOrder: () => void;
}

export function useSectionsLayout({
  transcripts,
  summaries,
  liveSectionTranscripts,
  isRecording,
  elapsedTime,
  selectedSummaryId,
  autoMode,
  transcription,
  currentSectionIndex,
  getSectionKey,
  formatText,
  t,
}: UseSectionsLayoutParams): UseSectionsLayoutResult {
  const [sectionOrder, setSectionOrder] = useState<number[]>([]);

  const transcriptsBySection = useMemo(() => {
    const map = new Map<number, Transcript[]>();
    for (const transcript of transcripts) {
      const list = map.get(transcript.sectionIndex) ?? [];
      list.push(transcript);
      map.set(transcript.sectionIndex, list);
    }
    return map;
  }, [transcripts]);

  const summariesBySection = useMemo(() => {
    const map = new Map<number, Summary>();
    for (const summary of summaries) {
      map.set(summary.sectionIndex, summary);
    }
    return map;
  }, [summaries]);

  const liveSectionTranscriptsKeys = useMemo(
    () =>
      Object.keys(liveSectionTranscripts)
        .map(Number)
        .sort((a, b) => a - b),
    [liveSectionTranscripts],
  );

  const summariesSectionIndices = useMemo(
    () => summaries.map((s) => s.sectionIndex).sort((a, b) => a - b),
    [summaries],
  );

  const transcriptsSectionIndices = useMemo(
    () => transcripts.map((t) => t.sectionIndex).sort((a, b) => a - b),
    [transcripts],
  );

  const updateSectionOrder = useCallback(() => {
    const sections = new Set<number>();

    transcriptsSectionIndices.forEach((sectionIndex) => sections.add(sectionIndex));
    summariesSectionIndices.forEach((sectionIndex) => sections.add(sectionIndex));
    liveSectionTranscriptsKeys.forEach((key) => sections.add(key));
    if (isRecording) {
      const sectionFromTime = Math.floor(elapsedTime / 30);
      const effectiveSection =
        currentSectionIndex != null
          ? Math.min(sectionFromTime, currentSectionIndex)
          : sectionFromTime;
      sections.add(effectiveSection);
    }
    if (sections.size === 0) sections.add(0);

    setSectionOrder((prev) => {
      const next = Array.from(sections).sort((a, b) => a - b);
      if (next.length === prev.length && next.every((value, i) => value === prev[i])) {
        return prev;
      }
      return next;
    });
  }, [
    elapsedTime,
    isRecording,
    liveSectionTranscriptsKeys,
    summariesSectionIndices,
    transcriptsSectionIndices,
  ]);

  const hasAnySectionData = sectionOrder.length > 0;

  const sectionsData: SectionData[] = useMemo(() => {
    return sectionOrder.map((sectionIndex) => {
      const sectionKey = getSectionKey(sectionIndex);
      const transcriptItems = transcriptsBySection.get(sectionIndex) ?? [];
      const transcriptText = transcriptItems
        .map((item) => formatText(item.text))
        .filter(Boolean)
        .join("\n");
      const liveTranscriptText = liveSectionTranscripts[sectionIndex] ?? "";
      const currentSection =
        currentSectionIndex != null ? currentSectionIndex : Math.floor(elapsedTime / 30);
      const isCurrentSection = isRecording && sectionIndex === currentSection;
      let displayText = [transcriptText, liveTranscriptText]
        .filter((text) => text && text.trim().length > 0)
        .join(transcriptText && liveTranscriptText ? "\n" : "");
      if (!displayText && isCurrentSection) {
        displayText = transcription;
      }
      if (!displayText) {
        displayText = t("session.noTranscript");
      }

      const summaryFromDb = summariesBySection.get(sectionIndex);
      const summaryKey = summaryFromDb?.id ?? -(sectionIndex + 1);
      const summaryText = formatText(summaryFromDb?.text) || t("session.noSummaryText");
      const isSelected = selectedSummaryId === summaryKey;

      const hasNoSummary = summaryText === t("session.noSummaryText");
      const isGenerating = summaryFromDb?.text === "요약 생성 중...";
      const isFinalSummary = summaryFromDb?.phase?.toUpperCase() === "FINAL";
      const isClickable = !hasNoSummary && !isGenerating && !autoMode && isFinalSummary;

      return {
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
      };
    });
  }, [
    autoMode,
    elapsedTime,
    formatText,
    getSectionKey,
    isRecording,
    liveSectionTranscripts,
    sectionOrder,
    selectedSummaryId,
    summariesBySection,
    t,
    transcription,
    transcriptsBySection,
  ]);

  return {
    sectionOrder,
    sectionsData,
    hasAnySectionData,
    updateSectionOrder,
  };
}
