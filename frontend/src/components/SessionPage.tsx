import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import SectionCard from "./SectionCard";
import StreamingResourceCard from "./StreamingResourceCard";
import StreamingQnACard from "./StreamingQnACard";
import { AnimatedLoaderIcon } from "./AnimatedLoaderIcon";
import { EndSessionModal } from "./EndSessionModal";
import { SessionHeader } from "./SessionHeader";
import { LecturePane } from "./LecturePane";
import { SplitPane } from "./SplitPane";
import { useBackend } from "../services/BackendContext";
import { useI18n } from "../i18n/I18nContext";
import type {
  Bookmark as BookmarkType,
  QnA,
  Resource,
  SessionDetailResponse,
  Summary,
  Transcript,
} from "../services/ports";
import type { StreamingCard } from "./StreamingCardTypes";
import { toast } from "sonner";
import { Client } from "@stomp/stompjs";
import { useSectionsLayout } from "../hooks/useSectionsLayout";
import { useRecording } from "../hooks/useRecording";

type SummaryPhase = 'partial' | 'final';

function groupBySection<T extends { sectionIndex: number }>(items?: T[]): Record<number, T[]> {
  if (!items) return {};
  return items.reduce<Record<number, T[]>>((acc, item) => {
    (acc[item.sectionIndex] = acc[item.sectionIndex] ?? []).push(item);
    return acc;
  }, {});
}

interface SessionPageProps {
  lectureId: number;
  onLogoClick: () => void;
  onSettings: () => void;
  onLogout: () => void;
  onSaveAndEnd: (sessionName: string) => Promise<void> | void;
}

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
  const finalSummaryRequestRef = useRef<Map<number, string>>(new Map());
const requestStreamingCardRef = useRef<Set<number>>(new Set()); // 섹션별 추가 카드 생성 요청 여부 추적
const cardRequestInFlightRef = useRef<Set<number>>(new Set()); // 동시 중복 요청 방지용
  const currentSectionIndexRef = useRef<number>(-1);
  const elapsedTimeRef = useRef<number>(0);
  const lectureScrollViewportRef = useRef<HTMLDivElement | null>(null);
  const sectionKeyMapRef = useRef<Map<number, string>>(new Map());
  const resourceScrollViewportRef = useRef<HTMLDivElement | null>(null);
  const qnaScrollViewportRef = useRef<HTMLDivElement | null>(null);
  const prevStreamingResourceCountRef = useRef<number>(0);
  const prevStreamingQnACountRef = useRef<number>(0);
  const [showEndModal, setShowEndModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<"settings" | "logout" | "home" | null>(null);
  const [splitMode, setSplitMode] = useState(false);
  const [selectedSummaryId, setSelectedSummaryId] = useState<number | null>(null);
  const [selectedSectionIndex, setSelectedSectionIndex] = useState<number | null>(null);
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  const [isGeneratingExtended, setIsGeneratingExtended] = useState(false); // 추가 생성 중인지 추적
  const [sectionScrollTrigger, setSectionScrollTrigger] = useState(0);
  const [hasRecordingStarted, setHasRecordingStarted] = useState(false);

  const [transcription, setTranscription] = useState("");
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [resourcesBySection, setResourcesBySection] = useState<Record<number, Resource[]>>({});
  const [qnaBySection, setQnaBySection] = useState<Record<number, QnA[]>>({});
  const [bookmarks, setBookmarks] = useState<BookmarkType[]>([]);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [liveSectionTranscripts, setLiveSectionTranscripts] = useState<Record<number, string>>({});
  const [serverSectionIndex, setServerSectionIndex] = useState(0);
  const [serverElapsedSec, setServerElapsedSec] = useState(0);

  // 새로운 섹션이 생기거나 내용이 갱신될 때 왼쪽 강의 뷰포트를 항상 맨 아래로 스크롤
  const stompClientRef = useRef<Client | null>(null);
  const [streamingCards, setStreamingCards] = useState<Map<string, StreamingCard>>(new Map());

  const {
    isRecording,
    isEnded,
    elapsedTime,
    currentSectionIndex,
    handleToggleRecording,
    hasRecordingStarted: recordingStartedFromHook,
  } = useRecording({
    lectureId,
    backend,
    t,
    serverSectionIndex,
    serverElapsedSec,
    onLiveTranscript: (sectionIndex, content, isFinal) => {
      setLiveSectionTranscripts((prev) => {
        const prevText = prev[sectionIndex] ?? "";
        const updatedText = isFinal
          ? prevText
            ? prevText + "\n" + content
            : content
          : (() => {
            if (!prevText) return content;
            const lines = prevText.split("\n");
            lines[lines.length - 1] = content;
            return lines.join("\n");
          })();

        if (
          sectionIndex === currentSectionIndexRef.current ||
          currentSectionIndexRef.current === -1
        ) {
          setTranscription(updatedText);
        }

        return {
          ...prev,
          [sectionIndex]: updatedText,
        };
      });
    },
    onRecordingStartedOnce: () => {
      setHasRecordingStarted(true);
    },
  });

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
    const normalized = items.map((item) => {
      const type = typeof item.type === "string" ? item.type.toLowerCase() as QnA["type"] : item.type;
      const summaryId = (item as any).summaryId ?? (item as any).summary_id ?? item.summaryId;
      return { ...item, type, summaryId };
    });
    setQnaBySection((prev) => {
      const existing = prev[sectionIndex] ?? [];
      const existingIds = new Set(existing.map((item) => item.id));
      const deduped = normalized.filter((item) => !existingIds.has(item.id));
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

  const {
    sectionOrder,
    sectionsData,
    hasAnySectionData,
    updateSectionOrder,
  } = useSectionsLayout({
    transcripts,
    summaries,
    liveSectionTranscripts,
    isRecording,
    elapsedTime,
    currentSectionIndex,
    selectedSummaryId,
    autoMode,
    transcription,
    getSectionKey,
    formatText,
    t,
  });
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

      // 강의 진행 시간 복원은 useRecording 훅 내부에서 관리
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : t("session.fetchError"));
    } finally {
      setLoading(false);
    }
  }, [backend, lectureId, t, formatText]);

  useEffect(() => {
    // 강의 새로고침 시 ref 초기화
    requestStreamingCardRef.current.clear();
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
    resourceType?: 'paper' | 'wiki' | 'video' | 'blog';
    title?: string;
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

        // Resource 추가 생성 카드도 유형 정보가 없으면 기본 스타일(그라데이션)로 표시
        let resourceType: 'paper' | 'wiki' | 'video' | 'blog' | undefined = message.resourceType;

        newMap.set(cardId, {
          cardId,
          type: type as 'qna' | 'resource',
          cardIndex,
          content: message.token || '',
          isComplete: message.isComplete,
          data: message.data,
          error: message.error,
          resourceType,
          title: message.title,
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
            let resourceType: 'paper' | 'wiki' | 'video' | 'blog' | undefined =
              message.resourceType || existingCard.resourceType;
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
              title: message.title ?? existingCard.title,
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


            if (!client || !client.connected) {
              console.error('[STOMP] 클라이언트가 연결되지 않았습니다');
              return;
            }

            // 각 타입별 토픽 구독
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
                if (data.sectionIndex !== undefined && Array.isArray(data.items)) {
                  replaceQnAForSection(data.sectionIndex, data.items);
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
                if (data.sectionIndex !== undefined && Array.isArray(data.items)) {
                  replaceResourcesForSection(data.sectionIndex, data.items);
                  // 카드 상태 업데이트는 제거 (불필요한 리렌더링 방지)
                }
              } catch (err) {
                console.error("자료 메시지 처리 오류", err);
              }
            });

            // 섹션 상태 구독
            client.subscribe(`/topic/lectures/${lectureId}/section`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (typeof data.sectionIndex === "number") {
                  setServerSectionIndex(data.sectionIndex);
                }
              } catch (err) {
                console.error("섹션 상태 메시지 처리 오류", err);
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

            // 전사 구독 (섹션/elapsed 동기화 및 transcripts 상태 업데이트)
            client.subscribe(`/topic/lectures/${lectureId}/transcripts`, (message) => {
              try {
                const data = JSON.parse(message.body);
                if (typeof data.sectionIndex === "number") {
                  setServerSectionIndex(data.sectionIndex);
                }
                if (typeof data.endSec === "number") {
                  setServerElapsedSec((prev) => Math.max(prev, data.endSec));
                }
                // DB 전사 목록에 반영
                const t: Transcript = {
                  id: Date.now(),
                  lectureId,
                  sectionIndex: data.sectionIndex ?? 0,
                  startSec: data.startSec ?? 0,
                  endSec: data.endSec ?? 0,
                  text: data.text ?? "",
                };
                setTranscripts((prev) => {
                  const exists = prev.some((p) => p.sectionIndex === t.sectionIndex && p.startSec === t.startSec && p.endSec === t.endSec && p.text === t.text);
                  return exists ? prev : [...prev, t];
                });
              } catch (err) {
                console.error("전사 메시지 처리 오류", err, message.body);
              }
            });
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
  }, [lectureId]);

  useEffect(() => {
    setLiveSectionTranscripts({});
    sectionKeyMapRef.current.clear();
    finalSummaryRequestRef.current.clear();
  }, [lectureId]);

  useEffect(() => {
    setHasRecordingStarted(false);
  }, [lectureId]);

  useEffect(() => {
    updateSectionOrder();
  }, [updateSectionOrder]);

  const requestStreamingCard = useCallback(
    (sectionIndex: number) => {
      // QnA 타입별로 스트리밍 시작 (4개: concept, application, advanced, comparison)
      const qnaTypes = ["concept", "application", "advanced", "comparison"];
      const qnaPromises = qnaTypes.map((qnaType, index) => {
        // cardIndex는 기존 완료된 카드 수를 고려하여 설정 (기본 2개: 0, 1 + 추가 인덱스)
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

      Promise.all([...qnaPromises, ...resourcePromises]).finally(() => {
        setIsGeneratingExtended(false);
      });
    },
    [backend, lectureId]
  );

  // summaries를 섹션 인덱스별로 빠르게 조회하기 위한 맵 (선택 상태 유지 등에 사용)
  const summariesBySection = useMemo(() => {
    const map = new Map<number, Summary>();
    for (const summary of summaries) {
      map.set(summary.sectionIndex, summary);
    }
    return map;
  }, [summaries]);


  // selectedSummaryId를 ref로 추적하여 의존성 문제 방지
  const selectedSummaryIdRef = useRef<number | null>(null);
  useEffect(() => {
    selectedSummaryIdRef.current = selectedSummaryId;
  }, [selectedSummaryId]);

  const handleSummaryClick = useCallback(
    async (summaryId: number, sectionIndex: number) => {
      if (cardRequestInFlightRef.current.has(sectionIndex)) {
        console.log(`[handleSummaryClick] 요청 진행 중인 섹션 → 스킵: section=${sectionIndex}`);
        return;
      }
      cardRequestInFlightRef.current.add(sectionIndex);

      // ref를 사용하여 현재 값 확인 (의존성 문제 방지)
      if (selectedSummaryIdRef.current === summaryId) {
        // 같은 요약을 다시 클릭하면 해제
        setSplitMode(false);
        setSelectedSummaryId(null);
        setSelectedSectionIndex(null);
        cardRequestInFlightRef.current.delete(sectionIndex);
        return;
      }

      // 1단계: DB에서 카드 개수 먼저 확인 (추가 요청 필요 여부 판단)
      let shouldRequestMore = false;
      try {
        const summary = summariesBySection.get(sectionIndex);
        const phase = summary?.phase?.toUpperCase();
        const isFinalSummary = phase ? phase === "FINAL" : true; // phase가 없으면 FINAL로 간주

        // FINAL 요약이 아니면 추가 카드 요청을 하지 않음
        if (!isFinalSummary) {
          console.log(`[handleSummaryClick] FINAL 요약 아님 → 추가 요청 생략: section=${sectionIndex}`);
          shouldRequestMore = false;
        }

        const cardsStatus = await backend.lecture.getCardsStatus(lectureId, sectionIndex);
        const existingQnaCount = cardsStatus.qnaCards.filter(c => c.isComplete).length;
        const existingResourceCount = cardsStatus.resourceCards.filter(c => c.isComplete).length;
        
        console.log(`[handleSummaryClick] sectionIndex=${sectionIndex}, QnA=${existingQnaCount}, Resource=${existingResourceCount}`);

        // QnA나 Resource 중 하나라도 3개 이상이면 이미 요청했으므로 요청 안 함 (API 제한 고려)
        if (existingQnaCount >= 3 || existingResourceCount >= 3) {
          console.log(`[handleSummaryClick] 이미 3개 이상 → 최초 클릭 아님, 요청 생략 (API 제한): section=${sectionIndex}`);
          shouldRequestMore = false;
        } else if (isFinalSummary && existingQnaCount <= 2 && existingResourceCount <= 2 && !requestStreamingCardRef.current.has(sectionIndex)) {
          // FINAL 최초 클릭: QnA ≤ 2, Resource ≤ 2 → 4개씩 요청
          // (PARTIAL로 2개 이하 생성되었거나, AI 서버 내부 로직으로 2개보다 적게 생성된 경우 포함)
          console.log(`[handleSummaryClick] FINAL 최초 클릭 (QnA≤2, Resource≤2) → 4개씩 요청: section=${sectionIndex}`);
          shouldRequestMore = true;
          requestStreamingCardRef.current.add(sectionIndex);
        } else {
          console.log(`[handleSummaryClick] 이미 요청했거나 조건 불일치: section=${sectionIndex}`);
          shouldRequestMore = false;
        }
      } catch (error) {
        console.error("카드 상태 확인 실패:", error);
        // 에러 발생 시에는 요청하지 않음 (DB 확인 없이는 중복 요청 방지 불가)
        shouldRequestMore = false;
      }

      // 2단계: UI 업데이트 (섹션 선택)
      setSelectedSectionIndex(sectionIndex);
      setSplitMode(true);
      setSelectedSummaryId(summaryId);

      // 3단계: 카드 표시 업데이트 (DB에서 가져와서 표시)
      updateCardsForSection(sectionIndex).catch(error => {
        console.error("카드 상태 업데이트 실패:", error);
      });

      // 4단계: 필요한 경우에만 추가 카드 요청
      if (shouldRequestMore) {
        setIsGeneratingExtended(true);
        requestStreamingCard(sectionIndex);
      }
      cardRequestInFlightRef.current.delete(sectionIndex);
    },
    [
      backend,
      lectureId,
      updateCardsForSection,
      requestStreamingCard,
      summariesBySection,
    ]
  );

  // 컴포넌트 마운트 시 ref 초기화 (재로그인 대응)
  useEffect(() => {
    console.log("[SessionPage] 컴포넌트 마운트: ref 초기화");
    requestStreamingCardRef.current.clear();
    finalSummaryRequestRef.current.clear();
    cardRequestInFlightRef.current.clear();
  }, []);

  useEffect(() => {
    setLiveSectionTranscripts({});
    requestStreamingCardRef.current.clear(); // 강의 변경 시 초기화
    finalSummaryRequestRef.current.clear();
    cardRequestInFlightRef.current.clear();
    setResourcesBySection({});
    setQnaBySection({});
  }, [lectureId]);

  useEffect(() => {
    summaries.forEach((summary) => {
      if (!summary || summary.phase?.toUpperCase() !== "FINAL") {
        return;
      }
      const signature = `${summary.id ?? `section-${summary.sectionIndex}`}:${Array.isArray(summary.text) ? summary.text.join(" ") : summary.text ?? ""}`;
      const stored = finalSummaryRequestRef.current.get(summary.sectionIndex);
      if (stored && stored !== signature) {
        finalSummaryRequestRef.current.delete(summary.sectionIndex);
      }
    });
  }, [summaries]);

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
  }, [transcripts, formatText, isRecording, currentSectionIndex]);

  useEffect(() => {
    elapsedTimeRef.current = elapsedTime;
  }, [elapsedTime]);

  useEffect(() => {
    if (!isRecording) {
      currentSectionIndexRef.current = -1;
      return;
    }
    const newSectionIndex = currentSectionIndex;
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
  }, [currentSectionIndex, isRecording]);

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

  const closeSplitMode = () => {
    setSplitMode(false);
    setSelectedSummaryId(null);
    setSelectedSectionIndex(null);
    setAutoMode(false);
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <SessionHeader
        lecture={lecture}
        lectureId={lectureId}
        isRecording={isRecording}
        elapsedTime={elapsedTime}
        isEnded={isEnded}
        onToggleRecording={handleToggleRecording}
        onLogoClickConfirm={() => {
          setPendingAction("home");
          setShowEndModal(true);
        }}
        onEndConfirm={() => {
          handleToggleRecording(false);
          setShowEndModal(true);
        }}
        onSettingsConfirm={() => {
          setPendingAction("settings");
          setShowEndModal(true);
        }}
        onLogoutConfirm={() => {
          setPendingAction("logout");
          setShowEndModal(true);
        }}
      />

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
                    className={`w-3 h-3 rounded-full transition-colors cursor-pointer ${showBookmarkedOnly
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
                      {!showBookmarkedOnly &&
                        !loading &&
                        (resourcesForView.length === 0 ||
                          (isGeneratingExtended &&
                            streamingResourcesForSection.length === 0)) && (
                          <div className="flex items-center justify-start gap-2 mt-[3px]">
                            <AnimatedLoaderIcon id="grad-resources" />
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
                              <Badge className="text-xs text-[rgb(255,255,255)] flex-shrink-0" style={{ background: 'linear-gradient(90deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)' }}>
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
                      {!showBookmarkedOnly &&
                        !loading &&
                        (qnaForView.length === 0 ||
                          (isGeneratingExtended &&
                            streamingQnAsForSection.length === 0)) && (
                          <div className="flex items-center justify-start gap-2 mt-1">
                            <AnimatedLoaderIcon id="grad-ai" />
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
