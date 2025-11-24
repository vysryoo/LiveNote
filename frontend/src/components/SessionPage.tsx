import { Button } from "./ui/button";
import {DropdownMenu,DropdownMenuContent,DropdownMenuItem,DropdownMenuTrigger,} from "./ui/dropdown-menu";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import {User, Settings, LogOut} from "lucide-react";
import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, memo } from "react";
// @ts-ignore - vite에서 이미지 import 지원
import logoImage from "../assets/logo.png";
import RecordingTabControl from './RecordingTabControl';
import { EndSessionModal } from './EndSessionModal';
import { useBackend } from "../services/BackendContext";
import { useI18n } from "../i18n/I18nContext";
import type {Bookmark as BookmarkType, QnA, Resource, SessionDetailResponse, Summary, Transcript} from "../services/ports";
import { toast } from "sonner";
import { Client } from '@stomp/stompjs';

type SummaryPhase = 'partial' | 'final';

function groupBySection<T extends { sectionIndex: number }>(items?: T[]): Record<number, T[]> {
  if (!items) return {};
  return items.reduce<Record<number, T[]>>((acc, item) => {
    (acc[item.sectionIndex] = acc[item.sectionIndex] ?? []).push(item);
    return acc;
  }, {});
}

const DEV_AUDIO_URL = (import.meta as any).env?.VITE_DEV_AUDIO_URL as string | undefined;

interface SessionPageProps {
  lectureId: number;
  onLogoClick: () => void;
  onSettings: () => void;
  onLogout: () => void;
  onSaveAndEnd: (sessionName: string) => Promise<void> | void;
}

// StreamingCard 타입 정의
interface StreamingCard {
  cardId: string;
  type: 'qna' | 'resource';
  cardIndex: number;
  content: string;
  isComplete: boolean;
  data?: QnA | Resource;
  error?: string;
  resourceType?: 'paper' | 'wiki' | 'video' | 'blog'; // Resource 타입 (선택적)
  title?: string; // Resource 제목 (선택적)
}

// 스트리밍 Resource 카드 컴포넌트 (메모이제이션으로 리렌더링 최소화)
const StreamingResourceCard = memo(({ card }: { card: StreamingCard }) => {
  if (card.error) {
    return (
      <div
        className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px] border-red-300"
      >
        <div className="flex items-start justify-between mb-3 flex-shrink-0">
          <Badge className="text-xs bg-red-500 text-white flex-shrink-0">
            생성 실패
          </Badge>
        </div>
        <div className="mb-3 flex-shrink-0">
          <p className="font-medium text-red-600">생성 실패</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          <p className="text-sm text-red-500">
            {card.error}
          </p>
        </div>
      </div>
    );
  }
  
  // 타입별 색상 결정
  // 1. card.resourceType이 있으면 사용
  // 2. 없으면 cardIndex 기반으로 추론 (추가 생성 카드: cardIndex >= 2)
  // 3. 기본 생성 카드(cardIndex < 2)는 기본 색상 사용
  let resourceType: 'paper' | 'wiki' | 'video' | 'blog' | null = card.resourceType || null;
  if (!resourceType && card.cardIndex >= 2) {
    // 추가 생성 카드: cardIndex 2, 3, 4, 5가 각각 paper, wiki, video, blog
    const resourceTypes: ('paper' | 'wiki' | 'video' | 'blog')[] = ['paper', 'wiki', 'video', 'blog'];
    resourceType = resourceTypes[(card.cardIndex - 2) % 4];
  }
  
  // 타입별 배지 색상
  const badgeStyle = resourceType
    ? resourceType === "paper"
      ? { background: "linear-gradient(90deg, #0c4997, #1e5fa8, #3b72dd, #4d82e0)" }
      : resourceType === "wiki"
        ? { background: "linear-gradient(90deg, #0c966b, #10b981, #34d399, #6ee7b7)" }
        : resourceType === "video"
          ? { background: "linear-gradient(90deg, #960c0c, #dc2626, #ef4444, #f87171)" }
          : { background: "linear-gradient(90deg, #3f0c96, #6366f1, #8b5cf6, #a78bfa)" }
    : { background: 'linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)' };
  
  // 제목 추출 우선순위:
  // 1. 완료된 데이터 (card.data.title)가 있으면 사용
  // 2. card.title이 있으면 사용
  // 3. 없으면 "생성 중..." 표시
  const getTitle = () => {
    if (card.data && 'title' in card.data) {
      const resource = card.data as Resource;
      const title = resource.title;
      if (title) {
        return Array.isArray(title) ? title.join(' ') : title;
      }
    }
    if (card.title) {
      return card.title;
    }
    return "생성 중...";
  };

  const title = getTitle();
  
  return (
    <div
      className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
    >
      <div className="flex items-start justify-between mb-3 flex-shrink-0">
        <Badge className="text-xs text-[rgb(255,255,255)] flex-shrink-0" style={badgeStyle}>
          생성 중...
        </Badge>
      </div>
      <div className="mb-3 flex-shrink-0">
        <p className="font-medium">{title}</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        <p className="text-sm text-muted-foreground">
          {card.content || '생성 중...'}
        </p>
      </div>
    </div>
  );
});

StreamingResourceCard.displayName = 'StreamingResourceCard';

// 섹션 카드 컴포넌트 Props 타입
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
const SectionCard = memo(({
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
  const finalDisplayText = !displayText && isCurrentSection ? transcription : displayText || t("session.noTranscript");

  return (
    <div key={sectionKey}>
      {/* 강의 기록 컴포넌트 */}
      <div className="rounded-lg p-6 bg-white mb-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-[16px]">
            {t("session.header.record")}
          </h4>
          {isCurrentSection && (
            <span className="text-xs font-semibold text-[#6A737D]">
              실시간
            </span>
          )}
        </div>
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {finalDisplayText}
        </p>
      </div>

      {/* 실시간 요약 컴포넌트 */}
      <div
        onClick={isClickable ? () => onSummaryClick(summaryKey, sectionIndex) : undefined}
        className={`rounded-lg p-6 transition-all relative ${
          isClickable
            ? "cursor-pointer"
            : "cursor-not-allowed opacity-60"
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
          <h4 className={isSelected ? "text-white" : ""}>
            {t("session.header.summary")}
          </h4>
        </div>
        {isGenerating ? (
          <div className="flex items-center gap-2">
            <svg
              viewBox="0 0 120 120"
              width="20"
              height="20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <defs>
                <linearGradient
                  id={`grad-summary-${sectionIndex}`}
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor="#63A4FF">
                    <animate
                      attributeName="stop-color"
                      values="#63A4FF;#639BEE;#83EAF1;#3B72DD;#4D82E0;#63A4FF"
                      dur="6s"
                      repeatCount="indefinite"
                    />
                  </stop>
                  <stop
                    offset="100%"
                    stopColor="#4D82E0"
                  >
                    <animate
                      attributeName="stop-color"
                      values="#4D82E0;#3B72DD;#83EAF1;#639BEE;#63A4FF;#4D82E0"
                      dur="6s"
                      repeatCount="indefinite"
                    />
                  </stop>
                </linearGradient>
              </defs>
              <g transform="translate(60 60)">
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  values="0;360;1080;1440;2160"
                  keyTimes="0;0.25;0.5;0.75;1"
                  dur="6s"
                  repeatCount="indefinite"
                  additive="sum"
                />
                <path fill={`url(#grad-summary-${sectionIndex})`}>
                  <animate
                    attributeName="d"
                    dur="6s"
                    repeatCount="indefinite"
                    values="
                      M0,-30 
                      C16.5,-30 30,-16.5 30,0 
                      C30,16.5 16.5,30 0,30 
                      C-16.5,30 -30,16.5 -30,0 
                      C-30,-16.5 -16.5,-30 0,-30 
                      Z;
                  
                      M0,-45 
                      C5,-45 45,-5 45,0 
                      C45,5 5,45 0,45 
                      C-5,45 -45,5 -45,0 
                      C-45,-5 -5,-45 0,-45 
                      Z;
                  
                      M0,-30 
                      C16.5,-30 30,-16.5 30,0 
                      C30,16.5 16.5,30 0,30 
                      C-16.5,30 -30,16.5 -30,0 
                      C-30,-16.5 -16.5,-30 0,-30 
                      Z;
                  
                      M0,-45 
                      C5,-45 45,-5 45,0 
                      C45,5 5,45 0,45 
                      C-5,45 -45,5 -45,0 
                      C-45,-5 -5,-45 0,-45 
                      Z;
                  
                      M0,-30 
                      C16.5,-30 30,-16.5 30,0 
                      C30,16.5 16.5,30 0,30 
                      C-16.5,30 -30,16.5 -30,0 
                      C-30,-16.5 -16.5,-30 0,-30 
                      Z
                    "
                  />
                </path>
              </g>
            </svg>
            <p
              className={`text-sm ${isSelected ? "text-white" : "text-muted-foreground"}`}
            >
              {summaryText}
            </p>
          </div>
        ) : (
          <p
            className={`text-sm ${isSelected ? "text-white" : "text-muted-foreground"} whitespace-pre-line`}
          >
            {summaryText}
          </p>
        )}
      </div>
    </div>
  );
}, (prevProps, nextProps) => {
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
});

SectionCard.displayName = 'SectionCard';

// 스트리밍 QnA 카드 컴포넌트 (메모이제이션으로 리렌더링 최소화)
const StreamingQnACard = memo(({ card }: { card: StreamingCard }) => {
  if (card.error) {
    return (
      <div
        className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px] border-red-300"
      >
        <div className="flex items-start justify-between mb-3 flex-shrink-0">
          <Badge className="text-xs bg-red-500 text-white flex-shrink-0">
            생성 실패
          </Badge>
        </div>
        <div className="mb-3 flex-shrink-0">
          <p className="font-medium text-red-600">생성 실패</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          <p className="text-sm text-red-500 whitespace-pre-line">
            {card.error}
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div
      className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
    >
      <div className="flex items-start justify-between mb-3 flex-shrink-0">
        <Badge className="text-xs text-[rgb(255,255,255)] flex-shrink-0" style={{
          background: 'linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)'
        }}>
          생성 중...
        </Badge>
      </div>
      <div className="mb-3 flex-shrink-0">
        <p className="font-medium">생성 중...</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {card.content || '생성 중...'}
        </p>
      </div>
    </div>
  );
});

StreamingQnACard.displayName = 'StreamingQnACard';

export function SessionPage({
  lectureId,
  onLogoClick,
  onSettings,
  onLogout,
  onSaveAndEnd,
}: SessionPageProps) {
  const backend = useBackend();
  const { t } = useI18n();
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  // Test
  const sourceNodeRef = useRef<AudioNode | null>(null);
  const devAudioEndedRef = useRef(false);
const summaryRequestStateRef = useRef<Record<number, { midRequested?: boolean; finalRequested?: boolean }>>({});
const extendedGenerationRequestedRef = useRef<Set<number>>(new Set()); // 섹션별 추가 카드 생성 요청 여부 추적
const currentSectionIndexRef = useRef<number>(-1);
const elapsedTimeRef = useRef<number>(0);
const lectureScrollViewportRef = useRef<HTMLDivElement | null>(null);
const sectionKeyMapRef = useRef<Map<number, string>>(new Map());
const resourceScrollViewportRef = useRef<HTMLDivElement | null>(null);
const qnaScrollViewportRef = useRef<HTMLDivElement | null>(null);
const prevStreamingResourceCountRef = useRef<number>(0);
const prevStreamingQnACountRef = useRef<number>(0);
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isEnded, setIsEnded] = useState(false);
  const [showEndModal, setShowEndModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<"settings" | "logout" | "home" | null>(null);
  const [splitMode, setSplitMode] = useState(false);
  const [selectedSummaryId, setSelectedSummaryId] = useState<number | null>(null);
  const [selectedSectionIndex, setSelectedSectionIndex] = useState<number | null>(null);
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  const [isGeneratingExtended, setIsGeneratingExtended] = useState(false); // 추가 생성 중인지 추적
const [sectionScrollTrigger, setSectionScrollTrigger] = useState(0);
const [sectionOrder, setSectionOrder] = useState<number[]>([]);
const [hasRecordingStarted, setHasRecordingStarted] = useState(false);

  const [transcription, setTranscription] = useState("");
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [resourcesBySection, setResourcesBySection] = useState<Record<number, Resource[]>>({});
  const [qnaBySection, setQnaBySection] = useState<Record<number, QnA[]>>({});
  const [bookmarks, setBookmarks] = useState<BookmarkType[]>([]);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [liveSectionTranscripts, setLiveSectionTranscripts] = useState<Record<number, string>>({});
  
  // STOMP 클라이언트 및 스트리밍 카드 상태
  const stompClientRef = useRef<Client | null>(null);
  const [streamingCards, setStreamingCards] = useState<Map<string, StreamingCard>>(new Map());

const formatText = useCallback((value: string | string[] | undefined) => {
  if (!value) return "";
  return Array.isArray(value) ? value.join(" ") : value;
}, []);

const getSectionKey = useCallback((sectionIndex: number) => {
    const existing = sectionKeyMapRef.current.get(sectionIndex);
    if (existing) return existing;
    const newKey = `section-${sectionIndex}-${sectionKeyMapRef.current.size}`;
    sectionKeyMapRef.current.set(sectionIndex, newKey);
    return newKey;
  }, []);

  const replaceResourcesForSection = useCallback((sectionIndex: number, items: Resource[]) => {
    setResourcesBySection((prev) => {
      const next = { ...prev };
      if (!items || items.length === 0) {
        delete next[sectionIndex];
      } else {
        next[sectionIndex] = items;
      }
      return next;
    });
  }, []);

  const appendResourcesForSection = useCallback((sectionIndex: number, items: Resource[]) => {
    if (!items || items.length === 0) return;
    setResourcesBySection((prev) => {
      const existing = prev[sectionIndex] ?? [];
      const existingIds = new Set(existing.map((item) => item.id));
      const deduped = items.filter((item) => !existingIds.has(item.id));
      if (deduped.length === 0) {
        return prev;
      }
      return {
        ...prev,
        [sectionIndex]: [...existing, ...deduped],
      };
    });
  }, []);

  const replaceQnAForSection = useCallback((sectionIndex: number, items: QnA[]) => {
    setQnaBySection((prev) => {
      const next = { ...prev };
      if (!items || items.length === 0) {
        delete next[sectionIndex];
      } else {
        next[sectionIndex] = items;
      }
      return next;
    });
  }, []);

  const appendQnAForSection = useCallback((sectionIndex: number, items: QnA[]) => {
    if (!items || items.length === 0) return;
    setQnaBySection((prev) => {
      const existing = prev[sectionIndex] ?? [];
      const existingIds = new Set(existing.map((item) => item.id));
      const deduped = items.filter((item) => !existingIds.has(item.id));
      if (deduped.length === 0) {
        return prev;
      }
      return {
        ...prev,
        [sectionIndex]: [...existing, ...deduped],
      };
    });
  }, []);
  useLayoutEffect(() => {
    if (sectionScrollTrigger === 0) return;
    const viewport = lectureScrollViewportRef.current;
    if (!viewport) return;

    const scrollToBottom = () => {
      viewport.scrollTop = viewport.scrollHeight;
    };

    scrollToBottom();
    const rafId = requestAnimationFrame(scrollToBottom);

    return () => {
      cancelAnimationFrame(rafId);
    };
  }, [sectionScrollTrigger]);

  const [lecture, setLecture] = useState<SessionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const liveSectionTranscriptsKeys = useMemo(() => {
    return Object.keys(liveSectionTranscripts).map(Number).sort((a, b) => a - b);
  }, [liveSectionTranscripts]);

  // summaries와 transcripts의 섹션 인덱스만 추적 (내용 변경 무시)
  const summariesSectionIndices = useMemo(() => {
    return summaries.map(s => s.sectionIndex).sort((a, b) => a - b);
  }, [summaries]);

  const transcriptsSectionIndices = useMemo(() => {
    return transcripts.map(t => t.sectionIndex).sort((a, b) => a - b);
  }, [transcripts]);

  const updateSectionOrder = useCallback(() => {
    const sections = new Set<number>();

    transcriptsSectionIndices.forEach((sectionIndex) => sections.add(sectionIndex));
    summariesSectionIndices.forEach((sectionIndex) => sections.add(sectionIndex));
    liveSectionTranscriptsKeys.forEach((key) => sections.add(key));
    if (isRecording) {
      sections.add(Math.floor(elapsedTime / 30));
    }
    if (sections.size === 0) sections.add(0);

    setSectionOrder((prev) => {
      const next = Array.from(sections).sort((a, b) => a - b);
      if (next.length === prev.length && next.every((value, i) => value === prev[i])) {
        return prev;
      }
      return next;
    });
  }, [elapsedTime, isRecording, liveSectionTranscriptsKeys, summariesSectionIndices, transcriptsSectionIndices]);

  const hasAnySectionData = sectionOrder.length > 0;

  const refreshLecture = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await backend.lecture.getLecture(lectureId);
      setLecture(detail);
      
      // summaries 업데이트: 실제 변경이 있을 때만 업데이트
      setSummaries((prev) => {
        const newSummaries = detail.summaries ?? [];
        // 길이가 다르면 업데이트
        if (prev.length !== newSummaries.length) {
          return newSummaries;
        }
        // 섹션 인덱스별로 맵 생성하여 비교
        const prevMap = new Map<number, Summary>(prev.map(s => [s.sectionIndex, s]));
        const newMap = new Map<number, Summary>(newSummaries.map(s => [s.sectionIndex, s]));
        
        // 섹션 인덱스가 다르면 업데이트
        if (prevMap.size !== newMap.size) {
          return newSummaries;
        }
        
        // 각 섹션의 내용이 다른지 확인
        let hasChanges = false;
        for (const [sectionIndex, newSummary] of newMap.entries()) {
          const oldSummary = prevMap.get(sectionIndex);
          if (!oldSummary) {
            hasChanges = true;
            break;
          }
          if (
            (oldSummary.id ?? undefined) !== (newSummary.id ?? undefined) ||
            formatText(oldSummary.text) !== formatText(newSummary.text)
          ) {
            hasChanges = true;
            break;
          }
        }
        return hasChanges ? newSummaries : prev;
      });
      
      // transcripts 업데이트: 실제 변경이 있을 때만 업데이트
      setTranscripts((prev) => {
        const newTranscripts = detail.transcripts ?? [];
        if (prev.length !== newTranscripts.length) {
          return newTranscripts;
        }
        // 섹션 인덱스별로 맵 생성하여 비교
        const prevMap = new Map<number, Transcript>(prev.map(t => [t.sectionIndex, t]));
        const newMap = new Map<number, Transcript>(newTranscripts.map(t => [t.sectionIndex, t]));
        
        if (prevMap.size !== newMap.size) {
          return newTranscripts;
        }
        
        let hasChanges = false;
        for (const [sectionIndex, newTranscript] of newMap.entries()) {
          const oldTranscript = prevMap.get(sectionIndex);
          if (!oldTranscript) {
            hasChanges = true;
            break;
          }
          if (
            oldTranscript.id !== newTranscript.id ||
            formatText(oldTranscript.text) !== formatText(newTranscript.text)
          ) {
            hasChanges = true;
            break;
          }
        }
        return hasChanges ? newTranscripts : prev;
      });
      
      setResourcesBySection(groupBySection(detail.resources));
      setQnaBySection(groupBySection(detail.qna));
      setBookmarks(detail.bookmarks ?? []);
      const hasPersistedRecordingData =
        (detail.transcripts?.length ?? 0) > 0 ||
        (detail.summaries?.length ?? 0) > 0 ||
        (detail.resources?.length ?? 0) > 0 ||
        (detail.qna?.length ?? 0) > 0;
      if (hasPersistedRecordingData) {
        setHasRecordingStarted(true);
      }
      
      // 강의 진행 시간 복원: recording 상태이면 시간만 복원 (일시정지 상태로 시작)
      if (detail.status === "recording") {
        // duration이 있으면 elapsedTime 복원, 없으면 transcripts/summaries 기반으로 추정
        if (detail.duration != null) {
          setElapsedTime(Math.floor(detail.duration));
        } else {
          // transcripts나 summaries의 마지막 섹션을 기반으로 추정
          const lastTranscriptSection = detail.transcripts && detail.transcripts.length > 0
            ? Math.max(...detail.transcripts.map(t => t.sectionIndex))
            : -1;
          const lastSummarySection = detail.summaries && detail.summaries.length > 0
            ? Math.max(...detail.summaries.map(s => s.sectionIndex))
            : -1;
          const lastSection = Math.max(lastTranscriptSection, lastSummarySection);
          if (lastSection >= 0) {
            // 마지막 섹션의 시작 시간 + 30초 (섹션 중간으로 추정)
            setElapsedTime((lastSection + 1) * 30);
          }
        }
        // isRecording은 false로 유지 (일시정지 상태)
        // 사용자가 재생 버튼을 누르면 handleToggleRecording에서 재개됨
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : t("session.fetchError"));
    } finally {
      setLoading(false);
    }
  }, [backend, lectureId, t, formatText]);

  useEffect(() => {
    refreshLecture();
  }, [refreshLecture]);

  // 카드 상태 업데이트 함수 (분할 모드에서 자동 업데이트용)
  // streamingCards를 ref로 관리하여 의존성 문제 해결
  const streamingCardsRef = useRef<Map<string, StreamingCard>>(new Map());
  
  // streamingCards 상태 변경 시 ref도 업데이트
  useEffect(() => {
    streamingCardsRef.current = streamingCards;
  }, [streamingCards]);

  const updateCardsForSection = useCallback(
    async (sectionIndex: number) => {
      try {
        // 해당 섹션에 스트리밍 중인 카드가 있는지 확인 (ref 사용)
        const currentStreamingCards = streamingCardsRef.current;
        const hasStreamingCards = (Array.from(currentStreamingCards.values()) as StreamingCard[]).some((card) => {
          const parts = card.cardId.split('_');
          const cardSectionIndex = parts.length >= 3 ? parseInt(parts[2]) : null;
          return cardSectionIndex === sectionIndex && !card.isComplete;
        });
        
        // 카드 상태 조회
        console.log(`[updateCardsForSection] 카드 상태 조회 시작: sectionIndex=${sectionIndex}`);
        const cardsStatus = await backend.lecture.getCardsStatus(lectureId, sectionIndex);
        console.log(`[updateCardsForSection] 카드 상태 응답:`, {
          qnaCards: cardsStatus.qnaCards.length,
          resourceCards: cardsStatus.resourceCards.length,
        });
        
        // 완료된 카드 즉시 표시
        const completedQnAs = cardsStatus.qnaCards
          .filter(card => card.isComplete && card.data)
          .map(card => card.data as QnA);
        
        const completedResources = cardsStatus.resourceCards
          .filter(card => card.isComplete && card.data)
          .map(card => card.data as Resource);
        
        console.log(`[updateCardsForSection] 완료된 카드: QnA=${completedQnAs.length}, Resource=${completedResources.length}`);
        
        // 스트리밍 중인 카드가 있으면 append만 사용 (리렌더링 방지)
        // 스트리밍 중인 카드가 없으면 replace 사용 (전체 교체)
        if (hasStreamingCards) {
          // 스트리밍 중: 완료된 카드만 추가 (기존 카드 유지)
          if (completedQnAs.length > 0) {
            appendQnAForSection(sectionIndex, completedQnAs);
          }
          if (completedResources.length > 0) {
            appendResourcesForSection(sectionIndex, completedResources);
          }
        } else {
          // 스트리밍 중이 아님: 전체 교체
          if (completedQnAs.length > 0) {
            replaceQnAForSection(sectionIndex, completedQnAs);
          }
          if (completedResources.length > 0) {
            replaceResourcesForSection(sectionIndex, completedResources);
          }
        }
      } catch (error) {
        console.error("카드 상태 업데이트 실패:", error);
      }
    },
    [
      backend,
      lectureId,
      replaceQnAForSection,
      replaceResourcesForSection,
      appendQnAForSection,
      appendResourcesForSection,
    ]
  );

  // 스트리밍 메시지 처리 (STOMP 클라이언트보다 먼저 정의)
  const handleStreamingMessage = useCallback((message: {
    type: string;
    cardId: string;
    token?: string;
    isComplete: boolean;
    data?: QnA | Resource;
    error?: string;
  }) => {
    const cardId = message.cardId;
    console.log('[handleStreamingMessage] 처리 시작', { cardId, type: message.type, hasToken: !!message.token, isComplete: message.isComplete });
    
    setStreamingCards(prev => {
      const newMap = new Map<string, StreamingCard>(prev);
      const existingCard = newMap.get(cardId);
      
      if (!existingCard) {
        // 새 카드 생성 (처음 토큰 수신 시)
        const [type, lectureIdStr, sectionIndexStr, cardIndexStr] = cardId.split('_');
        const cardIndex = parseInt(cardIndexStr);
        
        // Resource 타입 추론 (추가 생성 카드의 경우)
        let resourceType: 'paper' | 'wiki' | 'video' | 'blog' | undefined = undefined;
        if (type === 'resource' && cardIndex >= 2) {
          const resourceTypes: ('paper' | 'wiki' | 'video' | 'blog')[] = ['paper', 'wiki', 'video', 'blog'];
          resourceType = resourceTypes[(cardIndex - 2) % 4];
        }
        
        newMap.set(cardId, {
          cardId,
          type: type as 'qna' | 'resource',
          cardIndex,
          content: message.token || '',
          isComplete: message.isComplete,
          data: message.data,
          error: message.error,
          resourceType,
        });
      } else {
        if (message.isComplete) {
          // 에러가 있으면 에러 처리
          if (message.error) {
            console.error(`[handleStreamingMessage] 에러 발생: ${cardId}, 에러: ${message.error}`);
            // 에러 카드 업데이트
            newMap.set(cardId, {
              ...existingCard,
              isComplete: true,
              error: message.error,
            });
            // 에러 카드는 3초 후 자동 제거
            setTimeout(() => {
              setStreamingCards(prev => {
                const newMap = new Map(prev);
                newMap.delete(cardId);
                return newMap;
              });
            }, 3000);
            return newMap;
          }
          
          // 완료: 전체 데이터로 교체
          const finalData = message.data;
          
          if (finalData) {
            // 완료된 카드를 실제 데이터로 추가
            // finalData에 sectionIndex가 있으면 우선 사용, 없으면 cardId에서 파싱
            let sectionIndex: number;
            if (message.type === 'qna_stream') {
              const qna = finalData as QnA;
              sectionIndex = qna.sectionIndex !== undefined ? qna.sectionIndex : 
                (() => {
                  const parts = cardId.split('_');
                  return parts.length >= 3 ? parseInt(parts[2]) : (selectedSectionIndex || 0);
                })();
              appendQnAForSection(sectionIndex, [qna]);
              
              // 카드 상태 업데이트는 제거 (불필요한 리렌더링 방지)
              // 완료된 카드는 이미 appendQnAForSection으로 추가되었으므로 별도 업데이트 불필요
            } else if (message.type === 'resource_stream') {
              const resource = finalData as Resource;
              sectionIndex = resource.sectionIndex !== undefined ? resource.sectionIndex : 
                (() => {
                  const parts = cardId.split('_');
                  return parts.length >= 3 ? parseInt(parts[2]) : (selectedSectionIndex || 0);
                })();
              appendResourcesForSection(sectionIndex, [resource]);
              
              // 카드 상태 업데이트는 제거 (불필요한 리렌더링 방지)
              // 완료된 카드는 이미 appendResourcesForSection으로 추가되었으므로 별도 업데이트 불필요
              
              // 제목 정보 저장 (완료 직전에 제목 표시를 위해)
              if (existingCard && resource.title) {
                const title = Array.isArray(resource.title) ? resource.title.join(' ') : resource.title;
                newMap.set(cardId, {
                  ...existingCard,
                  title,
                  data: resource,
                });
              }
            }
          }
          
          // 스트리밍 카드에서 제거
          newMap.delete(cardId);
        } else if (message.token) {
          // 토큰 추가
          if (existingCard) {
            const newContent = (existingCard.content || '') + message.token;
            console.log(`[handleStreamingMessage] 토큰 추가: ${cardId}, 길이: ${newContent.length}`);
            
            // Resource 타입 정보 업데이트 (완료 데이터에서 타입 추출)
            let resourceType: 'paper' | 'wiki' | 'video' | 'blog' | undefined = existingCard.resourceType;
            if (message.data && existingCard.type === 'resource') {
              const resource = message.data as Resource;
              if (resource.type) {
                resourceType = resource.type as 'paper' | 'wiki' | 'video' | 'blog';
              }
            }
            
            newMap.set(cardId, {
              ...existingCard,
              content: newContent,
              resourceType,
            });
          } else {
            console.warn(`[handleStreamingMessage] 토큰 수신했지만 카드 없음: ${cardId}`);
          }
        } else {
          console.warn(`[handleStreamingMessage] 알 수 없는 메시지 형식:`, message);
        }
      }
      
      return newMap;
    });
  }, [selectedSectionIndex, appendQnAForSection, appendResourcesForSection, splitMode, updateCardsForSection]);

  // STOMP 클라이언트 초기화 및 토픽 구독 (선택적 - 실패해도 녹음은 가능)
  useEffect(() => {
    // STOMP 연결은 선택적이므로 실패해도 녹음에 영향 없음
    // 비동기로 처리하여 컴포넌트 렌더링을 블로킹하지 않음
    const initStomp = async () => {
      // 환경 변수에서 WebSocket URL 가져오기, 없으면 현재 페이지의 프로토콜/호스트 기반으로 생성
      const WS_BASE = (import.meta as any).env?.VITE_WS_URL || 
        (window.location.protocol === 'https:' ? 'wss://localhost:8080' : 'ws://localhost:8080');
      
        const brokerURL = `${WS_BASE}/ws`;
        console.log(`[STOMP] 연결 시도: ${brokerURL}`);
        
        try {
        const client = new Client({
          brokerURL: brokerURL,
          reconnectDelay: 5000,
          heartbeatIncoming: 4000,
          heartbeatOutgoing: 4000,
          debug: (str) => {
            console.log(`[STOMP Debug] ${str}`);
          },
          onConnect: () => {
            console.log('[STOMP] 연결 성공 ✅');
            console.log('[STOMP] 연결된 클라이언트:', client?.connected);
            console.log('[STOMP] 구독할 lectureId:', lectureId);
            
            if (!client || !client.connected) {
              console.error('[STOMP] 클라이언트가 연결되지 않았습니다');
              return;
            }
            
            // 각 타입별 토픽 구독
            // 전사 구독
            client.subscribe(`/topic/lectures/${lectureId}/transcripts`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (data.type === 'transcript' && data.data) {
                  const content = data.data.content;
                  const isFinal = data.data.isFinal || false;
                  if (content) {
                    const sectionIndex = currentSectionIndexRef.current >= 0
                      ? currentSectionIndexRef.current
                      : Math.max(Math.floor(elapsedTimeRef.current / 30), 0);
                    
                    setLiveSectionTranscripts((prev) => {
                      const prevText = prev[sectionIndex] ?? "";
                      const updatedText = isFinal
                        ? (prevText ? prevText + '\n' + content : content)
                        : (() => {
                            if (!prevText) return content;
                            const lines = prevText.split('\n');
                            lines[lines.length - 1] = content;
                            return lines.join('\n');
                          })();
                      
                      if (sectionIndex === currentSectionIndexRef.current || currentSectionIndexRef.current === -1) {
                        setTranscription(updatedText);
                      }
                      
                      return {
                        ...prev,
                        [sectionIndex]: updatedText,
                      };
                    });
                  }
                }
              } catch (err) {
                console.error("전사 메시지 처리 오류", err);
              }
            });

            // 요약 구독
            client.subscribe(`/topic/lectures/${lectureId}/summary`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (data.sectionIndex !== undefined) {
                  setSummaries((prev) => {
                    const existingIndex = prev.findIndex(s => s.sectionIndex === data.sectionIndex);
                    if (existingIndex >= 0) {
                      const updated = [...prev];
                      updated[existingIndex] = { ...updated[existingIndex], ...data };
                      return updated;
                    } else {
                      return [...prev, data];
                    }
                  });
                }
              } catch (err) {
                console.error("요약 메시지 처리 오류", err);
              }
            });

            // QnA 구독 (완료된 카드)
            client.subscribe(`/topic/lectures/${lectureId}/qna`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (data.sectionIndex !== undefined) {
                  appendQnAForSection(data.sectionIndex, [data]);
                  // 카드 상태 업데이트는 제거 (불필요한 리렌더링 방지)
                }
              } catch (err) {
                console.error("QnA 메시지 처리 오류", err);
              }
            });

            // 자료 구독 (완료된 카드)
            client.subscribe(`/topic/lectures/${lectureId}/resources`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (data.sectionIndex !== undefined) {
                  appendResourcesForSection(data.sectionIndex, [data]);
                  // 카드 상태 업데이트는 제거 (불필요한 리렌더링 방지)
                }
              } catch (err) {
                console.error("자료 메시지 처리 오류", err);
              }
            });

            // 스트리밍 카드 구독
            const streamSubscription = client.subscribe(`/topic/lectures/${lectureId}/stream`, (message) => {
              try {
                console.log('[STOMP] 스트리밍 메시지 수신 (raw):', message.body);
                const parsedMessage = JSON.parse(message.body);
                console.log('[STOMP] 스트리밍 메시지 수신 (parsed):', parsedMessage);
                handleStreamingMessage(parsedMessage);
              } catch (err) {
                console.error('[STOMP] 스트리밍 메시지 파싱 실패:', err, message.body);
              }
            });
            console.log('[STOMP] 스트리밍 토픽 구독 완료: /topic/lectures/' + lectureId + '/stream');
            console.log('[STOMP] 구독 객체:', streamSubscription);
          },
          onStompError: (frame) => {
            console.error('[STOMP] STOMP 에러:', frame);
            console.error('[STOMP] 에러 메시지:', frame?.headers?.['message'] || frame?.body || '알 수 없는 에러');
            // 에러가 발생해도 녹음은 계속 가능하도록 경고만 표시
            console.warn('[STOMP] STOMP 연결 실패 - 스트리밍 카드 기능만 사용 불가, 녹음은 정상 작동');
          },
          onWebSocketError: (event) => {
            console.error('[STOMP] WebSocket 에러 상세:', event);
            console.error('[STOMP] WebSocket 에러 타입:', event?.type);
            console.error('[STOMP] WebSocket 에러 타겟:', event?.target);
            if (event?.target) {
              const ws = event.target as WebSocket;
              console.error('[STOMP] WebSocket 상태:', ws.readyState, 'URL:', ws.url);
              console.error('[STOMP] WebSocket readyState 설명:', 
                ws.readyState === 0 ? 'CONNECTING' :
                ws.readyState === 1 ? 'OPEN' :
                ws.readyState === 2 ? 'CLOSING' :
                ws.readyState === 3 ? 'CLOSED' : 'UNKNOWN'
              );
            }
            // 에러가 발생해도 녹음은 계속 가능하도록 경고만 표시
            console.warn('[STOMP] WebSocket 연결 실패 - 스트리밍 카드 기능만 사용 불가, 녹음은 정상 작동');
            console.warn('[STOMP] 연결 URL 확인 필요:', brokerURL);
          },
          onDisconnect: () => {
            console.log('[STOMP] 연결 종료 ❌');
            console.log('[STOMP] 연결이 끊어졌습니다. 스트리밍 메시지를 받을 수 없습니다.');
          },
        });
        
        // 연결 시도 (비동기, 실패해도 녹음은 계속 가능)
        console.log(`[STOMP] 클라이언트 활성화 시작: ${brokerURL}`);
        client.activate();
        stompClientRef.current = client;
        
        // 연결 상태 확인을 위한 타이머
        setTimeout(() => {
          if (!client.connected) {
            console.warn(`[STOMP] 연결 타임아웃: ${brokerURL}`);
            console.warn('[STOMP] 백엔드 서버가 실행 중인지 확인하세요');
            console.warn('[STOMP] WebSocket 엔드포인트(/ws)가 올바르게 설정되었는지 확인하세요');
            console.warn('[STOMP] 브라우저 콘솔에서 WebSocket 연결 에러를 확인하세요');
          }
        }, 3000);
      } catch (error) {
        console.error('[STOMP] 클라이언트 초기화 실패:', error);
        console.error('[STOMP] 에러 상세:', error instanceof Error ? error.message : String(error));
        console.error('[STOMP] 스택 트레이스:', error instanceof Error ? error.stack : 'N/A');
        console.warn('[STOMP] 연결 실패 - 스트리밍 카드 기능만 사용 불가, 녹음은 정상 작동');
        console.warn(`[STOMP] 연결 시도 URL: ${brokerURL}`);
        // 연결 실패해도 계속 진행 (녹음은 별도 WebSocket 사용)
      }
    };
    
    // 비동기로 초기화 (렌더링 블로킹 방지)
    initStomp().catch(error => {
      console.error('STOMP 초기화 중 예외 발생:', error);
    });
    
    return () => {
      try {
        if (stompClientRef.current) {
          stompClientRef.current.deactivate();
        }
      } catch (error) {
        console.error('STOMP 클라이언트 비활성화 실패:', error);
      }
      stompClientRef.current = null;
    };
  }, [lectureId, appendQnAForSection, appendResourcesForSection, handleStreamingMessage]);

  useEffect(() => {
    setLiveSectionTranscripts({});
    summaryRequestStateRef.current = {};
    sectionKeyMapRef.current.clear();
    setSectionOrder([]);
  }, [lectureId]);

  useEffect(() => {
    setHasRecordingStarted(false);
  }, [lectureId]);

  useEffect(() => {
    updateSectionOrder();
  }, [updateSectionOrder]);

  const triggerExtendedGeneration = useCallback(
    (sectionIndex: number) => {
      // QnA 타입별로 스트리밍 시작 (4개: concept, application, advanced, comparison)
      const qnaTypes = ["concept", "application", "advanced", "comparison"];
      const qnaPromises = qnaTypes.map((qnaType, index) => {
        // cardIndex는 기존 완료된 카드 수를 고려하여 설정 (기본 2개 + 추가 인덱스)
        // 간단하게 2 + index로 설정 (기존 기본 카드가 0, 1이므로)
        const cardIndex = 2 + index;
        const cardId = `qna_${lectureId}_${sectionIndex}_${cardIndex}`;
        
        console.log(`[추가 생성] QnA 스트리밍 시작: type=${qnaType}, cardIndex=${cardIndex}, cardId=${cardId}`);
        
        return backend.lecture
          .startQnAStream(lectureId, sectionIndex, cardIndex, qnaType)
          .then((result) => {
            console.log(`[추가 생성] QnA 스트리밍 시작 성공: ${cardId}`, result);
            // 카드는 첫 STOMP 메시지 수신 시 생성됨
            return result;
          })
          .catch((error) => {
            console.error(`[추가 생성] QnA 스트리밍 시작 실패: ${cardId}`, error);
            throw error;
          });
      });

      // Resource 타입별로 스트리밍 시작 (4개: paper, wiki, video, blog)
      const resourceTypes = ["paper", "wiki", "video", "blog"];
      const resourcePromises = resourceTypes.map((resourceType, index) => {
        // cardIndex는 기존 완료된 카드 수를 고려하여 설정 (기본 2개 + 추가 인덱스)
        const cardIndex = 2 + index;
        const cardId = `resource_${lectureId}_${sectionIndex}_${cardIndex}`;
        
        console.log(`[추가 생성] Resource 스트리밍 시작: type=${resourceType}, cardIndex=${cardIndex}, cardId=${cardId}`);
        
        return backend.lecture
          .startResourceStream(lectureId, sectionIndex, cardIndex, resourceType)
          .then((result) => {
            console.log(`[추가 생성] Resource 스트리밍 시작 성공: ${cardId}`, result);
            // 카드는 첫 STOMP 메시지 수신 시 생성됨
            return result;
          })
          .catch((error) => {
            console.error(`[추가 생성] Resource 스트리밍 시작 실패: ${cardId}`, error);
            throw error;
          });
      });
    },
    [backend, lectureId]
  );


  // selectedSummaryId를 ref로 추적하여 의존성 문제 방지
  const selectedSummaryIdRef = useRef<number | null>(null);
  useEffect(() => {
    selectedSummaryIdRef.current = selectedSummaryId;
  }, [selectedSummaryId]);

  const handleSummaryClick = useCallback(
    async (summaryId: number, sectionIndex: number) => {
      // ref를 사용하여 현재 값 확인 (의존성 문제 방지)
      if (selectedSummaryIdRef.current === summaryId) {
        // 같은 요약을 다시 클릭하면 해제
        setSplitMode(false);
        setSelectedSummaryId(null);
        setSelectedSectionIndex(null);
        return;
      }


      setSelectedSectionIndex(sectionIndex);
      setSplitMode(true);

      setSelectedSummaryId(summaryId);
      updateCardsForSection(sectionIndex).catch(error => {
        console.error("카드 상태 업데이트 실패:", error);
      });

      if (!extendedGenerationRequestedRef.current.has(sectionIndex)) {
        extendedGenerationRequestedRef.current.add(sectionIndex);
        setIsGeneratingExtended(true);
        triggerExtendedGeneration(sectionIndex);
      } 
    },
    [
      backend,
      lectureId,
      updateCardsForSection,
      triggerExtendedGeneration,
    ]
  );

  useEffect(() => {
    setLiveSectionTranscripts({});
    summaryRequestStateRef.current = {};
    extendedGenerationRequestedRef.current.clear(); // 강의 변경 시 초기화
    setResourcesBySection({});
    setQnaBySection({});
  }, [lectureId]);

  // summaries 변경 시 selectedSummaryId 유지 (summaryKey가 변경되어도 선택 유지)
  // 예: id가 없는 요약(-(sectionIndex + 1))에서 id가 생긴 요약으로 변경될 때
  useEffect(() => {
    if (selectedSummaryId !== null && selectedSectionIndex !== null) {
      const summaryFromDb = summariesBySection.get(selectedSectionIndex);
      const currentSummaryKey = summaryFromDb?.id ?? -(selectedSectionIndex + 1);
      
      // summaryKey가 변경되었지만 같은 섹션이면 selectedSummaryId 업데이트
      // 단, selectedSummaryId가 음수(임시 키)이고 currentSummaryKey가 양수(실제 id)인 경우만 업데이트
      if (selectedSummaryId !== currentSummaryKey && 
          selectedSummaryId < 0 && 
          currentSummaryKey > 0) {
        // 같은 섹션의 요약이 id를 받았으면 새로운 summaryKey로 업데이트
        setSelectedSummaryId(currentSummaryKey);
      }
    }
  }, [summaries, selectedSummaryId, selectedSectionIndex, summariesBySection]);

  // 오토모드: 새로운 요약 완료 시 자동으로 카드 클릭
  const prevSummariesRef = useRef<Summary[]>([]);
  useEffect(() => {
    if (!autoMode || !splitMode) {
      prevSummariesRef.current = summaries;
      return;
    }

    // 새로운 완료된 요약 찾기
    const prevSummaryMap = new Map<number, Summary>(prevSummariesRef.current.map(s => [s.sectionIndex, s]));
    const newCompletedSummaries = summaries.filter((summary: Summary) => {
      const prevSummary = prevSummaryMap.get(summary.sectionIndex);
      const summaryText = formatText(summary.text);
      const prevSummaryText = prevSummary ? formatText(prevSummary.text) : null;
      const isNewlyCompleted = 
        summaryText && 
        summaryText !== "요약 생성 중..." &&
        summaryText !== t("session.noSummaryText") &&
        (!prevSummary || 
         !prevSummaryText ||
         prevSummaryText === "요약 생성 중..." || 
         prevSummaryText === t("session.noSummaryText") ||
         prevSummaryText !== summaryText);
      
      // 이미 선택된 섹션이 아니어야 함
      return isNewlyCompleted && summary.sectionIndex !== selectedSectionIndex;
    });

    // 가장 최근 섹션의 요약을 자동으로 클릭
    if (newCompletedSummaries.length > 0) {
      const latestSummary = newCompletedSummaries.reduce((latest, current) => 
        current.sectionIndex > latest.sectionIndex ? current : latest
      );
      const summaryKey = latestSummary.id ?? -(latestSummary.sectionIndex + 1);
      handleSummaryClick(summaryKey, latestSummary.sectionIndex);
    }

    prevSummariesRef.current = summaries;
  }, [summaries, autoMode, splitMode, selectedSectionIndex, handleSummaryClick, t]);

  // 분할 모드일 때 선택된 섹션의 카드 상태를 주기적으로 업데이트
  // 주의: 초기 로드는 handleSummaryClick에서 수행하므로 여기서는 주기적 업데이트만 수행
  useEffect(() => {
    if (splitMode && selectedSectionIndex !== null) {
      // 주기적으로 업데이트 (5초마다)
      // 단, 스트리밍 중인 카드가 있으면 업데이트 건너뛰기
      const interval = setInterval(() => {
        // 해당 섹션에 스트리밍 중인 카드가 있는지 확인 (ref 사용)
        const currentStreamingCards = streamingCardsRef.current;
        const hasStreamingCards = (Array.from(currentStreamingCards.values()) as StreamingCard[]).some((card) => {
          const parts = card.cardId.split('_');
          const cardSectionIndex = parts.length >= 3 ? parseInt(parts[2]) : null;
          return cardSectionIndex === selectedSectionIndex && !card.isComplete;
        });
        
        // 스트리밍 중인 카드가 없을 때만 업데이트
        if (!hasStreamingCards) {
          updateCardsForSection(selectedSectionIndex);
        }
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [splitMode, selectedSectionIndex, updateCardsForSection]);

  useEffect(() => {
    if (transcripts.length === 0) {
      return;
    }
    setLiveSectionTranscripts((prev) => {
      const next = { ...prev };
      let changed = false;
      const sectionsWithDb = new Set<number>();
      for (const transcript of transcripts) {
        sectionsWithDb.add(transcript.sectionIndex);
      }
      sectionsWithDb.forEach((sectionIndex) => {
        if (next[sectionIndex]) {
          delete next[sectionIndex];
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [transcripts]);


  // refreshLecture에서 이미 처리하므로 이 useEffect는 제거
  // useEffect(() => {
  //   if (!lecture) return;
  //   // 새 강의는 기본적으로 일시정지 상태에서 시작
  //   // lecture.status를 확인하되, 새로 생성된 강의는 false로 시작
  //   if (lecture.status === "recording" && !isRecording) {
  //     // 기존에 녹음 중이던 강의를 다시 열었을 때만 자동 재개
  //     // 새 강의는 사용자가 시작 버튼을 눌러야 함
  //   }
  // }, [lecture?.id, isRecording]);

  // transcripts가 변경되어도 실시간 전사 중이면 덮어쓰지 않음
  // 녹음이 끝나거나 transcripts가 비어있을 때만 초기화
  // 섹션이 바뀔 때는 이전 섹션의 전사본을 표시하기 위해 refreshLecture 호출
  useEffect(() => {
    // 녹음 중이면 현재 섹션의 실시간 전사를 유지 (덮어쓰지 않음)
    // 하지만 이전 섹션의 전사본은 DB에서 가져와서 summaries와 함께 표시됨
    if (isRecording) {
      // 녹음 중일 때는 현재 섹션의 실시간 전사만 표시
      // 이전 섹션의 전사본은 summaries.map()에서 transcriptsBySection을 통해 표시됨
      return;
    }
    
    // 녹음이 끝났을 때만 DB 전사로 초기화
    if (transcripts.length === 0) {
      setTranscription("");
      return;
    }
    
    // 현재 섹션의 전사만 가져오기 (전체가 아닌)
    const currentSectionIndex = Math.floor(elapsedTime / 30);
    const currentSectionTranscripts = transcripts.filter(t => t.sectionIndex === currentSectionIndex);
    
    if (currentSectionTranscripts.length > 0) {
      const joined = currentSectionTranscripts
        .map((item) => formatText(item.text))
        .filter(Boolean)
        .join("\n");
      setTranscription(joined);
    } else {
      setTranscription("");
    }
  }, [transcripts, formatText, isRecording, elapsedTime]);

  useEffect(() => {
    if (!isRecording) return;
    const timer = window.setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, [isRecording]);

  useEffect(() => {
    elapsedTimeRef.current = elapsedTime;
  }, [elapsedTime]);

  useEffect(() => {
    // refreshLecture에서 이미 처리하므로, 여기서는 recording 상태가 아닐 때만 처리
    if (lecture?.duration != null && lecture.status !== "recording") {
      setElapsedTime(Math.floor(lecture.duration));
    }
  }, [lecture?.duration, lecture?.status]);

  useEffect(() => {
    if (!isRecording) {
      currentSectionIndexRef.current = -1;
      return;
    }
    const newSectionIndex = Math.floor(elapsedTime / 30);
    if (newSectionIndex !== currentSectionIndexRef.current) {
      const previousSectionIndex = currentSectionIndexRef.current;
      currentSectionIndexRef.current = newSectionIndex;
      setTranscription("");
      setLiveSectionTranscripts((prev) => ({
        ...prev,
        [newSectionIndex]: prev[newSectionIndex] ?? "",
      }));
      setSectionScrollTrigger((prev) => prev + 1);
      console.log(`🔄 섹션 전환: ${previousSectionIndex} → ${newSectionIndex}`);
    }
  }, [elapsedTime, isRecording]);

  const isBookmarked = useCallback(
    (type: BookmarkType["targetType"], targetId: number) =>
      bookmarks.some((bookmark) => bookmark.targetType === type && bookmark.targetId === targetId),
    [bookmarks]
  );

  const toggleBookmark = useCallback(
    async (
      type: BookmarkType["targetType"],
      targetId: number,
      sectionIndex: number
    ) => {
      const existing = bookmarks.find(
        (bookmark) => bookmark.targetType === type && bookmark.targetId === targetId
      );
      try {
        if (existing) {
          await backend.lecture.deleteBookmark(existing.id);
          setBookmarks((prev) => prev.filter((bookmark) => bookmark.id !== existing.id));
          toast.success(t("session.bookmarkRemoved"));
        } else {
          const created = await backend.lecture.addBookmark({
            lectureId,
            sectionIndex,
            targetType: type,
            targetId,
          });
          setBookmarks((prev) => [...prev, created]);
          toast.success(t("session.bookmarkAdded"));
        }
      } catch (err) {
        console.error(err);
        toast.error(err instanceof Error ? err.message : t("session.bookmarkFailed"));
      }
    },
    [backend, bookmarks, lectureId, t]
  );

  const requestSectionSummary = useCallback(
    async (sectionIndex: number, phase: "partial" | "final") => {
      if (sectionIndex < 0) return;
      const state = summaryRequestStateRef.current[sectionIndex] ?? {};
      if (phase === "partial" && state.midRequested) {
        return;
      }
      if (phase === "final" && state.finalRequested) {
        return;
      }
      summaryRequestStateRef.current[sectionIndex] = {
        midRequested: state.midRequested || phase === "partial",
        finalRequested: state.finalRequested || phase === "final",
      };

      // 요약 생성 중 상태를 summaries에 추가
      if (phase === "partial") {
        setSummaries((prev) => {
          const existingIndex = prev.findIndex(s => s.sectionIndex === sectionIndex);
          if (existingIndex >= 0) {
            // 이미 존재하면 업데이트
            const updated = [...prev];
            updated[existingIndex] = {
              ...updated[existingIndex],
              text: "요약 생성 중...",
            };
            return updated;
          } else {
            // 없으면 추가
            return [...prev, {
              lectureId,
              sectionIndex,
              startSec: sectionIndex * 30,
              endSec: sectionIndex * 30 + 30,
              text: "요약 생성 중...",
            }];
          }
        });
      }

      try {
        const result = await backend.lecture.generateSummary(lectureId, sectionIndex, phase);
        if (result.success && result.summary) {
          setSummaries((prev) => {
            const existingIndex = prev.findIndex(s => s.sectionIndex === sectionIndex);
            if (existingIndex >= 0) {
              // 이미 존재하면 업데이트
              const updated = [...prev];
              updated[existingIndex] = {
                ...updated[existingIndex],
                ...result.summary,
              };
              return updated;
            } else {
              // 없으면 추가
              return [...prev, result.summary!];
            }
          });
        } else if (result.error) {
          console.error(`Summary generation failed (section ${sectionIndex}):`, result.error);
        }
      } catch (error) {
        console.error(`Summary generation error (section ${sectionIndex}):`, error);
      }
    },
    [backend, lectureId, refreshLecture]
  );

  useEffect(() => {
    if (!isRecording) return;
    const sectionIndex = Math.floor(elapsedTime / 30);
    const secondsIntoSection = elapsedTime % 30;

    if (secondsIntoSection === 15) {
      requestSectionSummary(sectionIndex, "partial");
    }

    if (secondsIntoSection === 0 && elapsedTime > 0) {
      const previousSection = sectionIndex - 1;
      if (previousSection >= 0) {
        requestSectionSummary(previousSection, "final");
      }
    }
  }, [elapsedTime, isRecording, requestSectionSummary]);

  // Test
  const stopSourceNode = useCallback(() => {
    if (!sourceNodeRef.current) {
      return;
    }
    if (sourceNodeRef.current instanceof AudioBufferSourceNode && !devAudioEndedRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch (err) {
        console.debug("[DEV_AUDIO] AudioBufferSourceNode stop error", err);
      }
    }
    try {
      sourceNodeRef.current.disconnect();
    } catch (err) {
      console.debug("Audio node disconnect error", err);
    }
    sourceNodeRef.current = null;
  }, []);


  const handleToggleRecording = useCallback(
    async (shouldRecord: boolean) => {
      if (shouldRecord) {
        setIsEnded(false);
        if (!hasRecordingStarted) {
          setHasRecordingStarted(true);
        }
        
      
        try {
          let stream: MediaStream | null = null;
          /* [MIC_MODE_ORIGINAL]
          stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
              channelCount: 1, // mono
              sampleRate: 24000, // 24kHz
              echoCancellation: true,
              noiseSuppression: true,
            }
          });
          audioStreamRef.current = stream;
          */

          console.info(`[DEV_AUDIO] Using file playback: ${DEV_AUDIO_URL}`);
          devAudioEndedRef.current = false;

          // AudioContext를 사용하여 PCM16 변환
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
          const targetSampleRate = 24000;
          const audioContext = new AudioContextClass({
            sampleRate: targetSampleRate, // OpenAI 요구사항: 24kHz (브라우저가 지원하지 않으면 기본값 사용)
          });
          audioContextRef.current = audioContext;

          const actualSampleRate = audioContext.sampleRate;
          const needsResampling = Math.abs(actualSampleRate - targetSampleRate) > 100; // 100Hz 이상 차이 시 리샘플링

          // ScriptProcessorNode로 오디오 데이터 처리 (4096 샘플 버퍼)
          const bufferSize = 4096;
          const scriptProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);
          scriptProcessorRef.current = scriptProcessor;

          // PCM16 변환 및 전송
          scriptProcessor.onaudioprocess = (event) => {
            if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
              return;
            }

            const inputBuffer = event.inputBuffer;
            let inputData = inputBuffer.getChannelData(0); // Float32Array (mono)
            
            // 리샘플링 (필요시)
            if (needsResampling) {
              const ratio = targetSampleRate / actualSampleRate;
              const outputLength = Math.round(inputData.length * ratio);
              const resampledData = new Float32Array(outputLength);
              
              for (let i = 0; i < outputLength; i++) {
                const srcIndex = i / ratio;
                const srcIndexFloor = Math.floor(srcIndex);
                const srcIndexCeil = Math.min(srcIndexFloor + 1, inputData.length - 1);
                const fraction = srcIndex - srcIndexFloor;
                
                // 선형 보간
                resampledData[i] = inputData[srcIndexFloor] * (1 - fraction) + inputData[srcIndexCeil] * fraction;
              }
              inputData = resampledData;
            }
            
            // Float32Array를 Int16Array로 변환 (PCM16)
            const pcm16Data = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              // Float32 [-1.0, 1.0] -> Int16 [-32768, 32767]
              const sample = Math.max(-1, Math.min(1, inputData[i]));
              pcm16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
            }

            // Int16Array를 ArrayBuffer로 변환하여 WebSocket으로 전송
            backend.lecture.sendAudioData(wsRef.current, pcm16Data.buffer);
          };
          
          let sourceNode: AudioNode | null = null;
          if (!DEV_AUDIO_URL) {
            throw new Error("DEV_AUDIO_URL이 설정되어 있지 않습니다.");
          }
          // [DEV_AUDIO] 파일 스트림 디코딩
          const response = await fetch(DEV_AUDIO_URL);
          if (!response.ok) {
            throw new Error(`DEV_AUDIO 파일 로드 실패: ${response.statusText}`);
          }
          const fileBuffer = await response.arrayBuffer();
          const decodedBuffer = await new Promise<AudioBuffer>((resolve, reject) => {
            audioContext.decodeAudioData(
              fileBuffer.slice(0),
              (buffer) => resolve(buffer),
              (error) => reject(error)
            );
          });
          const bufferSource = audioContext.createBufferSource();
          bufferSource.buffer = decodedBuffer;
          bufferSource.onended = () => {
            devAudioEndedRef.current = true;
            console.info("[DEV_AUDIO] Playback finished");
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.close(1000, "dev-audio-finished");
            }
          };
          sourceNode = bufferSource;
          sourceNodeRef.current = bufferSource;

          /* [MIC_MODE_ORIGINAL]
          else if (stream) {
            const micSource = audioContext.createMediaStreamSource(stream);
            sourceNode = micSource;
            sourceNodeRef.current = micSource;
          }
          */

          if (!sourceNode) {
            throw new Error("오디오 소스를 초기화할 수 없습니다.");
          }

          // 오디오 파이프라인 연결
          sourceNode.connect(scriptProcessor);
          scriptProcessor.connect(audioContext.destination); // 무음 출력 (필수)
          if (sourceNode instanceof AudioBufferSourceNode) {
            sourceNode.start();
          }

          // 웹소켓 연결
          let ws: WebSocket;
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            ws = wsRef.current;
          } else {
            ws = backend.lecture.connectTranscription(lectureId);
            wsRef.current = ws;
            
            // 웹소켓이 열릴 때까지 대기
            if (ws.readyState === WebSocket.CONNECTING) {
              await new Promise<void>((resolve, reject) => {
                const timeout = setTimeout(() => {
                  reject(new Error("WebSocket connection timeout"));
                }, 5000);
                
                const onOpen = () => {
                  clearTimeout(timeout);
                  ws.removeEventListener('open', onOpen);
                  ws.removeEventListener('error', onError);
                  resolve();
                };
                
                const onError = (event: Event) => {
                  clearTimeout(timeout);
                  ws.removeEventListener('open', onOpen);
                  ws.removeEventListener('error', onError);
                  console.error("Transcription websocket connection error", event);
                  reject(new Error("WebSocket connection failed"));
                };
                
                ws.addEventListener('open', onOpen);
                ws.addEventListener('error', onError);
              });
            }
            
            // WebSocket 메시지 수신 처리
            ws.onmessage = (event) => {
              try {
                const message = JSON.parse(event.data);
                
                if (message.type === 'transcript' && message.data) {
                  const content = message.data.content;
                  const isFinal = message.data.isFinal || false;
                  
                  if (content) {
                    console.log(`📝 실시간 전사 수신: isFinal=${isFinal}, content="${content.substring(0, 50)}..."`);
                    const sectionIndex =
                      currentSectionIndexRef.current >= 0
                        ? currentSectionIndexRef.current
                        : Math.max(Math.floor(elapsedTimeRef.current / 30), 0);
                    
                    setLiveSectionTranscripts((prev) => {
                      const prevText = prev[sectionIndex] ?? "";
                      const updatedText = isFinal
                        ? (prevText ? prevText + '\n' + content : content)
                        : (() => {
                            if (!prevText) {
                              return content;
                            }
                            const lines = prevText.split('\n');
                            lines[lines.length - 1] = content;
                            return lines.join('\n');
                          })();
                      
                      if (sectionIndex === currentSectionIndexRef.current || currentSectionIndexRef.current === -1) {
                        setTranscription(updatedText);
                      }
                      
                      return {
                        ...prev,
                        [sectionIndex]: updatedText,
                      };
                    });
                  }
                } else if (message.type === 'error' && message.data) {
                  console.error("WebSocket error:", message.data.error);
                  toast.error(message.data.error || t("session.wsError"));
                }
              } catch (err) {
                console.error("WebSocket message parse error", err);
              }
            };
            
            ws.onclose = () => {
              wsRef.current = null;
              setIsRecording(false);
              // 스트림 정리
              if (audioStreamRef.current) {
                audioStreamRef.current.getTracks().forEach(track => track.stop());
                audioStreamRef.current = null;
              }
              // AudioContext 정리
              if (scriptProcessorRef.current) {
                scriptProcessorRef.current.disconnect();
                scriptProcessorRef.current = null;
              }
              stopSourceNode();
              if (audioContextRef.current) {
                audioContextRef.current.close().catch(console.error);
                audioContextRef.current = null;
              }
            };
            
            ws.onerror = (event) => {
              console.error("Transcription websocket error", event);
              toast.error(t("session.wsError"));
              setIsRecording(false);
            };
          }

          setIsRecording(true);
        } catch (error) {
          console.error("Failed to start recording", error);
          toast.error(error instanceof Error && error.name === 'NotAllowedError' 
            ? t("session.micPermissionDenied")
            : t("session.recordingError"));
          
          // 정리
          if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach(track => track.stop());
            audioStreamRef.current = null;
          }
          if (scriptProcessorRef.current) {
            scriptProcessorRef.current.disconnect();
            scriptProcessorRef.current = null;
          }
          stopSourceNode();
          if (audioContextRef.current) {
            audioContextRef.current.close().catch(console.error);
            audioContextRef.current = null;
          }
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.close();
          }
          wsRef.current = null;
          setIsRecording(false);
        }
      } else {
        // 녹음 중지
        setIsRecording(false);
        
        // AudioContext 정리
        if (scriptProcessorRef.current) {
          scriptProcessorRef.current.disconnect();
          scriptProcessorRef.current = null;
        }
        stopSourceNode();
        if (audioContextRef.current) {
          audioContextRef.current.close().catch(console.error);
          audioContextRef.current = null;
        }

        // 오디오 스트림 정리
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach(track => track.stop());
          audioStreamRef.current = null;
        }

        // 웹소켓 연결 종료
        if (wsRef.current) {
          try {
            wsRef.current.close();
          } catch (error) {
            console.error("Failed to close transcription websocket", error);
          }
          wsRef.current = null;
        }
      }
    },
    [backend, hasRecordingStarted, lectureId, stopSourceNode, t]
  );


  useEffect(() => {
    return () => {
      // MediaRecorder 정리
      if (mediaRecorderRef.current) {
        try {
          if (mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
          }
        } catch (error) {
          console.error("Failed to stop MediaRecorder on cleanup", error);
        }
        mediaRecorderRef.current = null;
      }

      // 오디오 스트림 정리
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
        audioStreamRef.current = null;
      }

      // 웹소켓 정리
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (error) {
          console.error("Failed to close transcription websocket on cleanup", error);
        }
        wsRef.current = null;
      }
    };
  }, []);

  // 스트리밍 중인 카드 목록 메모이제이션 (리렌더링 최소화)
  const streamingResourcesForSection = useMemo(() => {
    if (selectedSectionIndex === null) return [];
    return (Array.from(streamingCards.values()) as StreamingCard[])
      .filter((card) => {
        const parts = card.cardId.split('_');
        const cardSectionIndex = parts.length >= 3 ? parseInt(parts[2]) : null;
        return card.type === 'resource' 
          && card.cardIndex !== undefined 
          && cardSectionIndex === selectedSectionIndex
          && !(card.isComplete && card.data)
          && !card.error; // 에러 카드 제외
      })
      .sort((a, b) => (a.cardIndex || 0) - (b.cardIndex || 0));
  }, [streamingCards, selectedSectionIndex]);

  const streamingQnAsForSection = useMemo(() => {
    if (selectedSectionIndex === null) return [];
    return (Array.from(streamingCards.values()) as StreamingCard[])
      .filter((card) => {
        const parts = card.cardId.split('_');
        const cardSectionIndex = parts.length >= 3 ? parseInt(parts[2]) : null;
        return card.type === 'qna' 
          && card.cardIndex !== undefined 
          && cardSectionIndex === selectedSectionIndex
          && !(card.isComplete && card.data)
          && !card.error; // 에러 카드 제외
      })
      .sort((a, b) => (a.cardIndex || 0) - (b.cardIndex || 0));
  }, [streamingCards, selectedSectionIndex]);

  const allResources = useMemo(() => Object.values(resourcesBySection).flat(), [resourcesBySection]);
  const resourcesForView = useMemo(() => {
    if (selectedSectionIndex == null) return allResources;
    const sectionResources = resourcesBySection[selectedSectionIndex];
    // 선택된 섹션의 리소스만 반환 (fallback 없이)
    return sectionResources || [];
  }, [resourcesBySection, selectedSectionIndex]);

  const allQnA = useMemo(() => Object.values(qnaBySection).flat(), [qnaBySection]);
  const qnaForView = useMemo(() => {
    if (selectedSectionIndex == null) return allQnA;
    const sectionQnA = qnaBySection[selectedSectionIndex];
    // 선택된 섹션의 QnA만 반환 (fallback 없이)
    return sectionQnA || [];
  }, [qnaBySection, selectedSectionIndex]);

  // 새로운 스트리밍 카드 도착 시 스크롤 맨 아래로 및 생성 상태 업데이트
  useEffect(() => {
    if (selectedSectionIndex === null) return;

    const currentResourceCount = streamingResourcesForSection.length;
    const currentQnACount = streamingQnAsForSection.length;
    
    // 스트리밍 카드가 도착하면 생성 중 상태 해제
    if (currentResourceCount > 0 || currentQnACount > 0) {
      setIsGeneratingExtended(false);
    }
    
    // Resource: 새로운 스트리밍 카드가 추가되면 스크롤 맨 아래로
    if (currentResourceCount > prevStreamingResourceCountRef.current) {
      setTimeout(() => {
        const viewport = resourceScrollViewportRef.current;
        if (viewport) {
          viewport.scrollTop = viewport.scrollHeight;
        }
      }, 100);
    }
    prevStreamingResourceCountRef.current = currentResourceCount;

    // QnA: 새로운 스트리밍 카드가 추가되면 스크롤 맨 아래로
    if (currentQnACount > prevStreamingQnACountRef.current) {
      setTimeout(() => {
        const viewport = qnaScrollViewportRef.current;
        if (viewport) {
          viewport.scrollTop = viewport.scrollHeight;
        }
      }, 100);
    }
    prevStreamingQnACountRef.current = currentQnACount;
  }, [streamingResourcesForSection.length, streamingQnAsForSection.length, selectedSectionIndex]);

  // 섹션별 데이터를 메모이제이션하여 계산
  const sectionsData = useMemo(() => {
    return sectionOrder.map((sectionIndex) => {
      const sectionKey = getSectionKey(sectionIndex);
      const transcriptItems = transcriptsBySection.get(sectionIndex) ?? [];
      const transcriptText = transcriptItems
        .map((item) => formatText(item.text))
        .filter(Boolean)
        .join("\n");
      const liveTranscriptText = liveSectionTranscripts[sectionIndex] ?? "";
      const isCurrentSection = isRecording && sectionIndex === Math.floor(elapsedTime / 30);
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
      const summaryText =
        formatText(summaryFromDb?.text) ||
        t("session.noSummaryText");
      const isSelected = selectedSummaryId === summaryKey;
      
      // 요약 상태 확인
      const hasNoSummary = summaryText === t("session.noSummaryText");
      const isGenerating = summaryFromDb?.text === "요약 생성 중...";
      // 요약 생성 중이거나 데이터가 없으면 클릭 불가능, 다음 섹션으로 넘어가면 클릭 가능
      // 오토모드일 때는 다른 카드는 클릭 불가능
      const isClickable = !hasNoSummary && !isGenerating && !autoMode;

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
    sectionOrder,
    transcriptsBySection,
    liveSectionTranscripts,
    transcription,
    summariesBySection,
    isRecording,
    elapsedTime,
    selectedSummaryId,
    autoMode,
    getSectionKey,
    formatText,
    t,
  ]);

  const closeSplitMode = () => {
    setSplitMode(false);
    setSelectedSummaryId(null);
    setSelectedSectionIndex(null);
    setAutoMode(false);
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b bg-white shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: 'clamp(14px, 1.2vw, 18px)' }}>
          <div className="flex justify-between items-center">
            <button
              onClick={() => {
                setPendingAction("home");
                setShowEndModal(true);
              }}
              className="flex items-center hover:opacity-80"
              style={{ gap: '0.8em' }}
            >
              <img
                src={logoImage}
                alt="LiveNote"
                style={{ height: '3em' }}
              />
              <span style={{ fontSize: '1.2em' }}>{lecture?.title ?? `세션 ${lectureId}`}</span>
            </button>

            <div className="flex items-center" style={{ gap: '1.2em' }}>
              {/* Controls */}
              <div className="flex items-center" style={{ gap: '0.6em' }}>
                <RecordingTabControl
                  isRecording={isRecording}
                  onToggle={handleToggleRecording}
                  elapsedTime={elapsedTime}
                  onEnd={() => {
                    handleToggleRecording(false);
                    setShowEndModal(true);
                  }}
                  isEnded={isEnded}
                />
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="rounded-full bg-[#f5f5f5] transition-all duration-300 [box-shadow:2px_2px_4px_#d8d8d8,-2px_-2px_4px_#ffffff] data-[state=open]:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] active:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] hover:bg-[#f5f5f5]"
                    style={{ width: '32px', height: '32px' }}
                  >
                    <User style={{ width: '16px', height: '16px' }} color="#6A737D" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => {
                      setPendingAction("settings");
                      setShowEndModal(true);
                    }}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    {t("common.settings")}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      setPendingAction("logout");
                      setShowEndModal(true);
                    }}
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    {t("common.logout")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex safe-scroll">
        {/* LEFT: Lecture Content (Always visible) */}
        <div
          className={`${!splitMode ? "w-full" : "w-1/3"} overflow-hidden p-6 transition-all duration-300`}
        >
          <div
            ref={lectureScrollViewportRef}
            className="h-full overflow-y-auto"
          >
            <div className="space-y-6 safe-scroll">
              {error && (
                <div className="bg-red-50 text-red-600 border border-red-200 rounded-lg p-4 text-sm">
                  {error}
                </div>
              )}
              {loading ? (
                <div className="text-center text-muted-foreground py-12">
                  {t("session.loading")}
                </div>
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
                    onSummaryClick={handleSummaryClick}
                    t={t}
                  />
                ))
              )}
            </div>
          </div>
        </div>

        {/* RIGHT: Split Mode Content (Resources + AI Q&A) */}
        {splitMode && (
          <div className="flex-1 p-2 flex items-center justify-center">
            <div className="w-full h-full rounded-xl overflow-hidden shadow-2xl flex flex-col">
              {/* macOS Window Bar */}
              <div
                className="flex items-center justify-between px-4 py-2 bg-[#333333]"
                style={{ height: "29px" }}
              >
                <div className="flex items-center gap-2">
                  <button
                    onClick={closeSplitMode}
                    className="w-3 h-3 rounded-full bg-[#FF605C] hover:bg-[#FF3B30] transition-colors cursor-pointer"
                    title="창 닫기"
                  />
                  <button
                    onClick={() =>
                      setShowBookmarkedOnly(!showBookmarkedOnly)
                    }
                    className={`w-3 h-3 rounded-full transition-colors cursor-pointer ${
                      showBookmarkedOnly 
                        ? "bg-[#FFBD44]" 
                        : "bg-[#FFBD44] hover:bg-[#FFB000]"
                    }`}
                    title="북마크 필터"
                  />
                  <button
                    onClick={() => setAutoMode(!autoMode)}
                    className="w-3 h-3 rounded-full transition-colors cursor-pointer border border-white/20"
                    style={autoMode 
                      ? { backgroundColor: '#66FFAA', boxShadow: '0 0 4px rgba(102,255,170,0.6)' }
                      : { backgroundColor: '#55EE99' }
                    }
                    onMouseEnter={(e) => {
                      if (autoMode) {
                        e.currentTarget.style.backgroundColor = '#88FFCC';
                      } else {
                        e.currentTarget.style.backgroundColor = '#66FFAA';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (autoMode) {
                        e.currentTarget.style.backgroundColor = '#66FFAA';
                      } else {
                        e.currentTarget.style.backgroundColor = '#55EE99';
                      }
                    }}
                    title={autoMode ? "오토모드 끄기" : "오토모드 켜기"}
                  />
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 flex overflow-hidden bg-white">
                {/* Resources Pane */}
                <div className="w-1/2 border-r p-[12px] flex flex-col bg-[#f9fafb]">
                  <h3 className="mb-2 text-[16px]">&nbsp;{t("session.resources")}</h3>

                  <ScrollArea className="flex-1 h-0">
                    <div 
                      ref={(el) => {
                        if (el) {
                          const viewport = el.closest('[data-slot="scroll-area"]')?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLDivElement;
                          if (viewport) {
                            resourceScrollViewportRef.current = viewport;
                          }
                        }
                      }}
                      className="flex flex-col gap-3 p-[0px]"
                    >
                      {/* 완료된 Resource 카드 먼저 표시 */}
                      {resourcesForView.map((resource) => {
                        const bookmarked = isBookmarked("resource", resource.id);
                        if (showBookmarkedOnly && !bookmarked) {
                          return null;
                        }
                        const resourceTitle = formatText(resource.title) || "제목 없음";
                        const resourceDescription = formatText(resource.text) || "설명이 없습니다.";
                        return (
                        <div
                          key={resource.id}
                          className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
                        >
                          <div className="flex items-start justify-between mb-3 flex-shrink-0">
                            <Badge
                              className="text-xs text-[rgb(255,255,255)] flex-shrink-0 self-center"
                              style={{
                                background: resource.type === "paper"
                                  ? "linear-gradient(90deg, #0c4997, #1e5fa8, #3b72dd, #4d82e0)"
                                  : resource.type === "wiki"
                                    ? "linear-gradient(90deg, #0c966b, #10b981, #34d399, #6ee7b7)"
                                    : resource.type === "video"
                                      ? "linear-gradient(90deg, #960c0c, #dc2626, #ef4444, #f87171)"
                                      : "linear-gradient(90deg, #3f0c96, #6366f1, #8b5cf6, #a78bfa)"
                              }}
                            >
                              {resource.type === "paper"
                                ? "학술자료"
                                : resource.type === "wiki"
                                  ? "위키백과"
                                  : resource.type === "video"
                                    ? "유튜브"
                                    : "웹/블로그"}
                            </Badge>
                            <label className="ml-2 flex-shrink-0">
                              <input
                                type="checkbox"
                                id={`checkboxInput-resource-${resource.id}`}
                                checked={bookmarked}
                                onChange={() =>
                                  toggleBookmark(
                                    "resource",
                                    resource.id,
                                    resource.sectionIndex
                                  )
                                }
                              />
                              <label htmlFor={`checkboxInput-resource-${resource.id}`} className="bookmark scale-[0.6] text-[rgb(163,172,183)]">
                                <svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 384 512" className="svgIcon">
                                  <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"></path>
                                </svg>
                              </label>
                            </label>
                          </div>
                          <div className="mb-3 flex-shrink-0">
                            <p className="font-medium">
                              {resourceTitle}
                            </p>
                          </div>
                          <div className="flex-1 overflow-y-auto">
                            <p className="text-sm text-muted-foreground">
                              {resourceDescription}
                            </p>
                          </div>
                          <div className="pt-3 text-right text-xs text-muted-foreground">
                            <a href={resource.url} target="_blank" rel="noreferrer" className="underline">
                              자세히 보기
                            </a>
                          </div>
                        </div>
                      );
                      })}
                      {/* 스트리밍 중인 Resource 카드 표시 (완료된 카드 아래에) */}
                      {streamingResourcesForSection.map((streamingCard) => (
                        <StreamingResourceCard key={streamingCard.cardId} card={streamingCard} />
                      ))}
                      {!showBookmarkedOnly && !loading && 
                       (resourcesForView.length === 0 || 
                        (isGeneratingExtended && streamingResourcesForSection.length === 0)) && (
                        <div className="flex items-center justify-start gap-2 mt-[3px]">
                          <svg
                            viewBox="0 0 120 120"
                            width="20"
                            height="20"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <defs>
                              <linearGradient
                                id="grad-resources"
                                x1="0%"
                                y1="0%"
                                x2="100%"
                                y2="100%"
                              >
                                <stop offset="0%" stopColor="#63A4FF">
                                  <animate
                                    attributeName="stop-color"
                                    values="#63A4FF;#639BEE;#83EAF1;#3B72DD;#4D82E0;#63A4FF"
                                    dur="6s"
                                    repeatCount="indefinite"
                                  />
                                </stop>
                                <stop
                                  offset="100%"
                                  stopColor="#4D82E0"
                                >
                                  <animate
                                    attributeName="stop-color"
                                    values="#4D82E0;#3B72DD;#83EAF1;#639BEE;#63A4FF;#4D82E0"
                                    dur="6s"
                                    repeatCount="indefinite"
                                  />
                                </stop>
                              </linearGradient>
                            </defs>
                            <g transform="translate(60 60)">
                              <animateTransform
                                attributeName="transform"
                                type="rotate"
                                values="0;360;1080;1440;2160"
                                keyTimes="0;0.25;0.5;0.75;1"
                                dur="6s"
                                repeatCount="indefinite"
                                additive="sum"
                              />
                              <path fill="url(#grad-resources)">
                                <animate
                                  attributeName="d"
                                  dur="6s"
                                  repeatCount="indefinite"
                                  values="
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z;
                              
                                    M0,-45 
                                    C5,-45 45,-5 45,0 
                                    C45,5 5,45 0,45 
                                    C-5,45 -45,5 -45,0 
                                    C-45,-5 -5,-45 0,-45 
                                    Z;
                              
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z;
                              
                                    M0,-45 
                                    C5,-45 45,-5 45,0 
                                    C45,5 5,45 0,45 
                                    C-5,45 -45,5 -45,0 
                                    C-45,-5 -5,-45 0,-45 
                                    Z;
                              
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z
                                  "
                                />
                              </path>
                            </g>
                          </svg>
                          <span className="text-[rgb(125,128,136)] text-xs text-[14px]">
                            자료를 찾고 있습니다...
                          </span>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>

                {/* AI Q&A Pane */}
                <div className="w-1/2 p-[12px] flex flex-col bg-[#f9fafb]">
                  <h3 className="mb-2 text-[16px]">&nbsp;{t("session.ai")}</h3>

                  <ScrollArea className="flex-1 h-0">
                    <div 
                      ref={(el) => {
                        if (el) {
                          const viewport = el.closest('[data-slot="scroll-area"]')?.querySelector('[data-slot="scroll-area-viewport"]') as HTMLDivElement;
                          if (viewport) {
                            qnaScrollViewportRef.current = viewport;
                          }
                        }
                      }}
                      className="flex flex-col gap-3 p-[0px]"
                    >
                      {/* 완료된 QnA 카드 먼저 표시 */}
                      {qnaForView.map((qa) => {
                        const bookmarked = isBookmarked("qna", qa.id);
                        if (showBookmarkedOnly && !bookmarked) {
                          return null;
                        }
                        const typeLabel = qa.type === "concept"
                          ? "개념확인"
                          : qa.type === "application"
                            ? "응용확장"
                            : qa.type === "advanced"
                              ? "심화질의"
                              : "비교분석";
                        return (
                        <div
                          key={qa.id}
                          className="border rounded-lg p-6 bg-white opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col h-[325px]"
                        >
                          <div className="flex items-start justify-between mb-3 flex-shrink-0">
                            <Badge className="text-xs text-[rgb(255,255,255)] flex-shrink-0" style={{background: 'linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)'}}>
                              {typeLabel}
                            </Badge>
                            <label className="ml-2 flex-shrink-0">
                              <input
                                type="checkbox"
                                id={`checkboxInput-ai-${qa.id}`}
                                checked={bookmarked}
                                onChange={() =>
                                  toggleBookmark(
                                    "qna",
                                    qa.id,
                                    qa.sectionIndex
                                  )
                                }
                              />
                              <label htmlFor={`checkboxInput-ai-${qa.id}`} className="bookmark scale-[0.6]">
                                <svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 384 512" className="svgIcon">
                                  <path d="M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z"></path>
                                </svg>
                              </label>
                            </label>
                          </div>
                          <div className="mb-3 flex-shrink-0">
                            <p className="font-medium">
                              {Array.isArray(qa.question) ? qa.question.join('\n') : qa.question}
                            </p>
                          </div>
                          <div className="flex-1 overflow-y-auto">
                            <p className="text-sm text-muted-foreground whitespace-pre-line">
                              {Array.isArray(qa.answer) ? qa.answer.join('\n') : qa.answer}
                            </p>
                          </div>
                        </div>
                      );
                      })}
                      {/* 스트리밍 중인 QnA 카드 표시 (완료된 카드 아래에) */}
                      {streamingQnAsForSection.map((streamingCard) => (
                        <StreamingQnACard key={streamingCard.cardId} card={streamingCard} />
                      ))}
                      {!showBookmarkedOnly && !loading && 
                       (qnaForView.length === 0 || 
                        (isGeneratingExtended && streamingQnAsForSection.length === 0)) && (
                        <div className="flex items-center justify-start gap-2 mt-1">
                          <svg
                            viewBox="0 0 120 120"
                            width="20"
                            height="20"
                            xmlns="http://www.w3.org/2000/svg"
                          >
                            <defs>
                              <linearGradient
                                id="grad-ai"
                                x1="0%"
                                y1="0%"
                                x2="100%"
                                y2="100%"
                              >
                                <stop offset="0%" stopColor="#63A4FF">
                                  <animate
                                    attributeName="stop-color"
                                    values="#63A4FF;#639BEE;#83EAF1;#3B72DD;#4D82E0;#63A4FF"
                                    dur="6s"
                                    repeatCount="indefinite"
                                  />
                                </stop>
                                <stop
                                  offset="100%"
                                  stopColor="#4D82E0"
                                >
                                  <animate
                                    attributeName="stop-color"
                                    values="#4D82E0;#3B72DD;#83EAF1;#639BEE;#63A4FF;#4D82E0"
                                    dur="6s"
                                    repeatCount="indefinite"
                                  />
                                </stop>
                              </linearGradient>
                            </defs>
                            <g transform="translate(60 60)">
                              <animateTransform
                                attributeName="transform"
                                type="rotate"
                                values="0;360;1080;1440;2160"
                                keyTimes="0;0.25;0.5;0.75;1"
                                dur="6s"
                                repeatCount="indefinite"
                                additive="sum"
                              />
                              <path fill="url(#grad-ai)">
                                <animate
                                  attributeName="d"
                                  dur="6s"
                                  repeatCount="indefinite"
                                  values="
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z;
                              
                                    M0,-45 
                                    C5,-45 45,-5 45,0 
                                    C45,5 5,45 0,45 
                                    C-5,45 -45,5 -45,0 
                                    C-45,-5 -5,-45 0,-45 
                                    Z;
                              
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z;
                              
                                    M0,-45 
                                    C5,-45 45,-5 45,0 
                                    C45,5 5,45 0,45 
                                    C-5,45 -45,5 -45,0 
                                    C-45,-5 -5,-45 0,-45 
                                    Z;
                              
                                    M0,-30 
                                    C16.5,-30 30,-16.5 30,0 
                                    C30,16.5 16.5,30 0,30 
                                    C-16.5,30 -30,16.5 -30,0 
                                    C-30,-16.5 -16.5,-30 0,-30 
                                    Z
                                  "
                                />
                              </path>
                            </g>
                          </svg>
                          <span className="text-[rgb(125,128,136)] text-xs text-[14px]">
                            AI가 질문을 생성하고 있습니다...
                          </span>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      <EndSessionModal
        open={showEndModal}
        onClose={() => {
          setShowEndModal(false);
          setPendingAction(null);
        }}
        onSaveAndEnd={async (name) => {
          handleToggleRecording(false);
          try {
            await onSaveAndEnd(name);
            setIsEnded(true);
            setShowEndModal(false);
            if (pendingAction === "settings") {
              onSettings();
            } else if (pendingAction === "logout") {
              onLogout();
            } else if (pendingAction === "home") {
              onLogoClick();
            }
          } finally {
            setPendingAction(null);
          }
        }}
        defaultName={lecture?.title ?? ""}
      />
    </div>
  );
}