import type { Summary, Transcript } from "./api/schemas";
import type { LiveTranscript } from "./state/sessionReducer";

export type SectionView = {
  sectionIndex: number;
  transcriptText: string;
  summaryText: string;
  isFinalSummary: boolean;
  isCurrent: boolean;
  isSelected: boolean;
  isClickable: boolean;
};

/**
 * 저장된 전사와 실시간 전사를 한 섹션의 표시용 줄 목록으로 합친다.
 *
 * 확정 문장은 오디오 연결과 `/transcripts` 메시지 양쪽으로 들어오므로, 저장본에 이미 있는 문장은 실시간 쪽에서 뺀다.
 * 새로고침 전에 저장된 문장과 이후 실시간으로 들어온 문장이 모두 남는다.
 *
 * @param savedTexts 저장된 전사 문장 (시간순)
 * @param live 녹음 중 받은 실시간 전사. 없으면 저장본만 사용
 * @returns 표시할 줄 목록
 */
export function mergeTranscriptLines(savedTexts: string[], live?: LiveTranscript): string[] {
  const lines = savedTexts.map((text) => text.trim()).filter(Boolean);
  if (!live) return lines;
  const remaining = [...lines];
  for (const line of live.lines) {
    const trimmed = line.trim();
    const index = remaining.indexOf(trimmed);
    if (index >= 0) {
      remaining.splice(index, 1);
    } else if (trimmed) {
      lines.push(trimmed);
    }
  }
  if (live.pending?.trim()) lines.push(live.pending.trim());
  return lines;
}

/**
 * 세션 화면 왼쪽에 표시할 섹션 목록을 만든다.
 *
 * @param input.transcripts 저장된 전사
 * @param input.summaries 저장된 요약
 * @param input.liveTranscripts 섹션별 실시간 전사
 * @param input.currentSection 서버가 알려 준 현재 섹션
 * @param input.isRecording 녹음 중 여부. 녹음 중이면 전사가 없어도 현재 섹션을 표시
 * @param input.selectedSectionIndex 분할 화면에서 선택된 섹션
 * @param input.autoMode 오토 모드 여부. 켜져 있으면 직접 선택할 수 없음
 * @returns 섹션 번호 오름차순 목록
 */
export function buildSectionViews(input: {
  transcripts: Transcript[];
  summaries: Summary[];
  liveTranscripts: Record<number, LiveTranscript>;
  currentSection: number;
  isRecording: boolean;
  selectedSectionIndex: number | null;
  autoMode: boolean;
}): SectionView[] {
  const sectionIndexes = new Set<number>([
    ...input.transcripts.map((t) => t.sectionIndex),
    ...input.summaries.map((s) => s.sectionIndex),
    ...Object.keys(input.liveTranscripts).map(Number),
  ]);
  if (input.isRecording) sectionIndexes.add(input.currentSection);

  return [...sectionIndexes]
    .sort((a, b) => a - b)
    .map((sectionIndex) => {
      const savedTexts = input.transcripts
        .filter((t) => t.sectionIndex === sectionIndex)
        .map((t) => t.text);
      const summary = input.summaries.find((s) => s.sectionIndex === sectionIndex);
      const summaryText = summary?.text.trim() ?? "";
      const isFinalSummary = summary?.phase === "final" && summaryText !== "";
      return {
        sectionIndex,
        transcriptText: mergeTranscriptLines(savedTexts, input.liveTranscripts[sectionIndex]).join(
          "\n",
        ),
        summaryText,
        isFinalSummary,
        isCurrent: input.isRecording && sectionIndex === input.currentSection,
        isSelected: sectionIndex === input.selectedSectionIndex,
        // 확정 요약만 분할 화면을 열 수 있고, 오토 모드 중에는 자동 선택만 허용
        isClickable: isFinalSummary && !input.autoMode,
      };
    });
}
