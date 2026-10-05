import { useEffect, useEffectEvent, useLayoutEffect, useReducer, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { useEndLecture } from "@/features/lectures/hooks/useLectureMutations";
import type { Bookmark } from "../api/schemas";
import { RecordingError, useAudioRecording } from "../audio/useAudioRecording";
import { useBookmarkToggle } from "../hooks/useBookmarks";
import { useElapsedSeconds } from "../hooks/useElapsedSeconds";
import { useExtendedCards } from "../hooks/useExtendedCards";
import { useCurrentSection, useSessionDetail } from "../hooks/useSessionDetail";
import { useSessionStream } from "../realtime/useSessionStream";
import { buildSectionViews } from "../sectionViews";
import { initialSessionState, sessionReducer } from "../state/sessionReducer";
import { EndSessionDialog } from "./EndSessionDialog";
import { LecturePane } from "./LecturePane";
import { RecordingControl } from "./RecordingControl";
import { SessionHeader } from "./SessionHeader";
import { SplitPane } from "./SplitPane";

const SECTION_SECONDS = 30;

// 세션을 떠나는 동작은 모두 종료 대화창을 거친 뒤 실행
type LeaveAction = "end" | "home" | "settings" | "logout";

export function SessionPage() {
  const lectureId = Number(useParams().lectureId);
  if (!Number.isInteger(lectureId)) return <Navigate to="/lectures" replace />;
  // 강의가 바뀌면 녹음 연결과 실시간 상태를 모두 새로 만들기 위해 재마운트
  return <SessionView key={lectureId} lectureId={lectureId} />;
}

function SessionView({ lectureId }: { lectureId: number }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useLogout();
  const endMutation = useEndLecture();
  const detailQuery = useSessionDetail(lectureId);
  const currentSection = useCurrentSection(lectureId);
  const [liveState, dispatch] = useReducer(sessionReducer, initialSessionState);
  const [manualSection, setManualSection] = useState<number | null>(null);
  const [autoMode, setAutoMode] = useState(false);
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false);
  const [leaveAction, setLeaveAction] = useState<LeaveAction | null>(null);
  const scrollViewportRef = useRef<HTMLDivElement>(null);

  useSessionStream({
    lectureId,
    dispatch,
    onStreamError: () => toast.error(t("session.streamFailed")),
  });

  const recording = useAudioRecording({
    lectureId,
    onTranscript: (content, isFinal) =>
      dispatch({
        type: "LIVE_TRANSCRIPT_RECEIVED",
        sectionIndex: currentSection,
        content,
        isFinal,
      }),
    onInterrupted: (reason) =>
      toast.error(
        t(
          reason === "serverError"
            ? "session.transcriptionServerError"
            : "session.recordingInterrupted",
        ),
      ),
  });

  const detail = detailQuery.data;
  const transcripts = detail?.transcripts ?? [];
  const summaries = detail?.summaries ?? [];
  const bookmarks = detail?.bookmarks ?? [];
  const extendedCards = useExtendedCards(lectureId);
  const toggleBookmark = useBookmarkToggle(lectureId, bookmarks);

  // 오토 모드에서는 확정 요약이 있는 가장 최근 섹션을 자동으로 선택
  const finalSectionIndexes = summaries
    .filter((s) => s.phase === "final" && s.text.trim())
    .map((s) => s.sectionIndex);
  const latestFinalSection = finalSectionIndexes.length ? Math.max(...finalSectionIndexes) : null;
  const selectedSection = autoMode ? (latestFinalSection ?? manualSection) : manualSection;

  const requestCardsForAutoSelection = useEffectEvent((sectionIndex: number) =>
    extendedCards.request(sectionIndex),
  );
  useEffect(() => {
    if (autoMode && latestFinalSection !== null) requestCardsForAutoSelection(latestFinalSection);
  }, [autoMode, latestFinalSection]);

  const serverSeconds = Math.max(
    currentSection * SECTION_SECONDS,
    ...transcripts.map((transcript) => transcript.endSec ?? 0),
  );
  const elapsedSeconds = useElapsedSeconds(
    recording.isRecording && recording.isAudioActive,
    serverSeconds,
  );

  const sections = buildSectionViews({
    transcripts,
    summaries,
    liveTranscripts: liveState.liveTranscripts,
    currentSection,
    isRecording: recording.isRecording,
    selectedSectionIndex: selectedSection,
    autoMode,
  });

  // 새 섹션이 시작되면 왼쪽 목록을 맨 아래로 내려 현재 섹션을 보여 줌
  useLayoutEffect(() => {
    if (!recording.isRecording) return;
    const viewport = scrollViewportRef.current;
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [currentSection, recording.isRecording]);

  const startRecording = async () => {
    try {
      await recording.start();
    } catch (error) {
      const isPermissionDenied =
        error instanceof RecordingError && error.reason === "micPermissionDenied";
      toast.error(t(isPermissionDenied ? "session.micPermissionDenied" : "session.recordingError"));
    }
  };

  const selectSection = (sectionIndex: number) => {
    if (sectionIndex === selectedSection) {
      setManualSection(null);
      return;
    }
    setManualSection(sectionIndex);
    extendedCards.request(sectionIndex);
  };

  const closeSplit = () => {
    setManualSection(null);
    setAutoMode(false);
  };

  const requestLeave = (action: LeaveAction) => {
    recording.stop();
    setLeaveAction(action);
  };

  const saveAndEnd = async (title: string) => {
    await endMutation.mutateAsync({ lectureId, title });
    const action = leaveAction;
    setLeaveAction(null);
    toast.success(t("lectures.toast.ended"));
    if (action === "settings") navigate("/settings");
    else if (action === "logout") logout();
    else navigate("/lectures");
  };

  const isBookmarked = (targetType: Bookmark["targetType"], targetId: number) =>
    bookmarks.some((b) => b.targetType === targetType && b.targetId === targetId);
  const streamingCards = Object.values(liveState.streamingCards)
    .filter((card) => card.sectionIndex === selectedSection)
    .sort((a, b) => a.cardIndex - b.cardIndex);

  const hasRecordingData =
    recording.isRecording ||
    sections.length > 0 ||
    (detail?.qna.length ?? 0) > 0 ||
    (detail?.resources.length ?? 0) > 0;
  const status = detailQuery.isPending
    ? "loading"
    : detailQuery.isError
      ? "error"
      : hasRecordingData
        ? "ready"
        : "notStarted";

  return (
    <div className="h-screen flex flex-col bg-background">
      <SessionHeader
        title={detail?.title || t("lectures.untitled")}
        recordingControl={
          <RecordingControl
            isRecording={recording.isRecording}
            elapsedSeconds={elapsedSeconds}
            onStart={() => void startRecording()}
            onPause={recording.stop}
            onEnd={() => requestLeave("end")}
          />
        }
        onLogoClick={() => requestLeave("home")}
        onSettingsClick={() => requestLeave("settings")}
        onLogoutClick={() => requestLeave("logout")}
      />

      <div className="flex-1 overflow-hidden flex safe-scroll">
        <LecturePane
          status={status}
          sections={sections}
          isSplit={selectedSection !== null}
          scrollViewportRef={scrollViewportRef}
          onSummaryClick={selectSection}
        />
        {selectedSection !== null && (
          <SplitPane
            resources={(detail?.resources ?? []).filter((r) => r.sectionIndex === selectedSection)}
            qna={(detail?.qna ?? []).filter((q) => q.sectionIndex === selectedSection)}
            streamingResources={streamingCards.filter((card) => card.kind === "resource")}
            streamingQna={streamingCards.filter((card) => card.kind === "qna")}
            isGenerating={extendedCards.pendingSectionIndex === selectedSection}
            showBookmarkedOnly={showBookmarkedOnly}
            autoMode={autoMode}
            isBookmarked={isBookmarked}
            onToggleBookmark={toggleBookmark}
            onClose={closeSplit}
            onToggleBookmarkedOnly={() => setShowBookmarkedOnly((value) => !value)}
            onToggleAutoMode={() => setAutoMode((value) => !value)}
          />
        )}
      </div>

      <EndSessionDialog
        open={leaveAction !== null}
        defaultTitle={detail?.title ?? ""}
        onCancel={() => setLeaveAction(null)}
        onSaveAndEnd={saveAndEnd}
      />
    </div>
  );
}
