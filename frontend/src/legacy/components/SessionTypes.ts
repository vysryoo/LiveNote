export interface SectionData {
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
}
