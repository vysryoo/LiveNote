import { useLayoutEffect, useReducer, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useParams } from "react-router";
import { toast } from "sonner";
import { RecordingError, useAudioRecording } from "../audio/useAudioRecording";
import { useBookmarks } from "../hooks/useBookmarks";
import { useElapsedSeconds } from "../hooks/useElapsedSeconds";
import { useExtendedCards } from "../hooks/useExtendedCards";
import { useLeaveSession } from "../hooks/useLeaveSession";
import { useSectionSelection } from "../hooks/useSectionSelection";
import { useSessionDetail } from "../hooks/useSessionDetail";
import { useSessionStream } from "../realtime/useSessionStream";
import {
  buildSectionViews,
  estimateServerSeconds,
  resolveCurrentSection,
  toPaneStatus,
} from "../sectionViews";
import { initialSessionState, selectStreamingCards, sessionReducer } from "../state/sessionReducer";
import { EndSessionDialog } from "./EndSessionDialog";
import { LecturePane } from "./LecturePane";
import { RecordingControl } from "./RecordingControl";
import { SessionHeader } from "./SessionHeader";
import { SplitPane } from "./SplitPane";

export function SessionPage() {
  const lectureId = Number(useParams().lectureId);
  if (!Number.isInteger(lectureId)) return <Navigate to="/lectures" replace />;
  // 강의가 바뀌면 녹음 연결과 실시간 상태를 모두 새로 만들기 위해 재마운트
  return <SessionView key={lectureId} lectureId={lectureId} />;
}

function SessionView({ lectureId }: { lectureId: number }) {
  const { t } = useTranslation();
  const detailQuery = useSessionDetail(lectureId);
  const [liveState, dispatch] = useReducer(sessionReducer, initialSessionState);
  const currentSection = resolveCurrentSection(liveState.announcedSection, detailQuery.data);
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false);
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
  const extendedCards = useExtendedCards(lectureId);
  const bookmarks = useBookmarks(lectureId, detail?.bookmarks ?? []);
  const selection = useSectionSelection(summaries, extendedCards.request);
  const leave = useLeaveSession(lectureId, recording.stop);
  const { selectedSection } = selection;

  const elapsedSeconds = useElapsedSeconds(
    recording.isRecording && recording.isAudioActive,
    estimateServerSeconds(currentSection, transcripts),
  );

  const sections = buildSectionViews({
    transcripts,
    summaries,
    liveTranscripts: liveState.liveTranscripts,
    currentSection,
    isRecording: recording.isRecording,
    selectedSectionIndex: selectedSection,
    autoMode: selection.autoMode,
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

  const streamingCards = selectStreamingCards(liveState, selectedSection);
  const status = toPaneStatus(
    detailQuery,
    recording.isRecording ||
      sections.length > 0 ||
      (detail?.qna.length ?? 0) > 0 ||
      (detail?.resources.length ?? 0) > 0,
  );

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
            onEnd={() => leave.request("end")}
          />
        }
        onLogoClick={() => leave.request("home")}
        onSettingsClick={() => leave.request("settings")}
        onLogoutClick={() => leave.request("logout")}
      />

      <div className="flex-1 overflow-hidden flex">
        <LecturePane
          status={status}
          sections={sections}
          isSplit={selectedSection !== null}
          scrollViewportRef={scrollViewportRef}
          onSummaryClick={selection.select}
        />
        {selectedSection !== null && (
          <SplitPane
            key={selectedSection}
            resources={(detail?.resources ?? []).filter((r) => r.sectionIndex === selectedSection)}
            qna={(detail?.qna ?? []).filter((q) => q.sectionIndex === selectedSection)}
            streamingResources={streamingCards.resource}
            streamingQna={streamingCards.qna}
            isGenerating={extendedCards.pendingSectionIndex === selectedSection}
            showBookmarkedOnly={showBookmarkedOnly}
            autoMode={selection.autoMode}
            isBookmarked={bookmarks.isBookmarked}
            onToggleBookmark={bookmarks.toggle}
            onClose={selection.close}
            onToggleBookmarkedOnly={() => setShowBookmarkedOnly((value) => !value)}
            onToggleAutoMode={selection.toggleAutoMode}
          />
        )}
      </div>

      <EndSessionDialog
        open={leave.isConfirming}
        defaultTitle={detail?.title ?? ""}
        onCancel={leave.cancel}
        onSaveAndEnd={leave.saveAndEnd}
      />
    </div>
  );
}
