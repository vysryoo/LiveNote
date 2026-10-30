import type { SessionDetail, Summary, Transcript } from "./api/schemas";
import type { LiveTranscript } from "./state/sessionReducer";

export type SectionView = {
  sectionIndex: number;
  transcriptText: string;
  summaryText: string;
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
        isCurrent: input.isRecording && sectionIndex === input.currentSection,
        isSelected: sectionIndex === input.selectedSectionIndex,
        // 확정 요약만 분할 화면을 열 수 있고, 오토 모드 중에는 자동 선택만 허용
        isClickable: isFinalSummary && !input.autoMode,
      };
    });
}

// 백엔드가 섹션을 30초 단위로 나눔 (SectionAggregationService.SECTION_SEC)
const SECTION_SECONDS = 30;

export type PaneStatus = "loading" | "error" | "notStarted" | "ready";

/**
 * 확정 요약이 있는 가장 최근 섹션을 찾는다. 오토 모드가 이 섹션을 자동으로 선택한다.
 *
 * @param summaries 저장된 요약
 * @returns 섹션 번호. 확정 요약이 없으면 `null`
 */
export function findLatestFinalSection(summaries: Summary[]): number | null {
  const indexes = summaries
    .filter((s) => s.phase === "final" && s.text.trim())
    .map((s) => s.sectionIndex);
  return indexes.length ? Math.max(...indexes) : null;
}

/**
 * 서버 데이터로 확인된 녹음 경과 시간을 구한다.
 *
 * @param currentSection 현재 섹션 번호. 섹션 시작 시각까지는 지났다고 봄
 * @param transcripts 저장된 전사
 * @returns 현재 섹션 시작 시각과 저장된 전사의 마지막 끝 시각 중 큰 값(초)
 */
export function estimateServerSeconds(currentSection: number, transcripts: Transcript[]): number {
  return Math.max(
    currentSection * SECTION_SECONDS,
    ...transcripts.map((transcript) => transcript.endSec ?? 0),
  );
}

/**
 * 세션 화면 왼쪽 목록에 무엇을 보여 줄지 정한다.
 *
 * @param query 강의 상세 조회 상태
 * @param hasRecordingData 녹음 중이거나 표시할 섹션·카드가 하나라도 있는지
 * @returns 로딩, 오류, 녹음 시작 전, 표시 중 하나
 */
export function toPaneStatus(
  query: { isPending: boolean; isError: boolean },
  hasRecordingData: boolean,
): PaneStatus {
  if (query.isPending) return "loading";
  if (query.isError) return "error";
  return hasRecordingData ? "ready" : "notStarted";
}

/**
 * 녹음 중인 현재 섹션 번호를 구한다.
 *
 * `/section` 메시지는 섹션이 바뀔 때만 오므로 새로고침 직후에는 받은 번호가 없다. 저장된 데이터의 마지막 섹션과
 * 비교해 큰 값을 쓰므로, 받은 번호가 없어도 새 섹션의 첫 전사가 저장되면 그 섹션을 따라간다.
 *
 * @param announcedSection `/section` 메시지로 받은 번호. 받은 적이 없으면 0
 * @param detail 강의 상세. 받기 전이면 `undefined`
 * @returns 현재 섹션 번호
 */
export function resolveCurrentSection(
  announcedSection: number,
  detail: Pick<SessionDetail, "transcripts" | "summaries"> | undefined,
): number {
  if (!detail) return announcedSection;
  const savedIndexes = [...detail.transcripts, ...detail.summaries].map(
    (item) => item.sectionIndex,
  );
  return Math.max(announcedSection, ...savedIndexes);
}
