import "./RecordingControl.css";
import { Pause, Play, Square } from "lucide-react";

type RecordingControlProps = {
  isRecording: boolean;
  elapsedSeconds: number;
  onStart: () => void;
  onPause: () => void;
  onEnd: () => void;
};

function formatElapsed(totalSeconds: number) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((n) => n.toString().padStart(2, "0")).join(":");
}

/**
 * 녹음 시작·일시정지·종료 탭을 표시한다. 선택된 탭에 경과 시간을 표시한다.
 *
 * @param props.elapsedSeconds 표시할 경과 시간(초). 시간 계산은 호출부가 담당
 */
export function RecordingControl({
  isRecording,
  elapsedSeconds,
  onStart,
  onPause,
  onEnd,
}: RecordingControlProps) {
  const elapsed = <span style={{ color: "#6A737D" }}>{formatElapsed(elapsedSeconds)}</span>;
  return (
    <div className="recording-tab-container">
      <input
        type="radio"
        name="recording-tab"
        id="recording-tab1"
        className="recording-tab recording-tab--1"
        checked={isRecording}
        onChange={onStart}
      />
      <label className="recording-tab_label" htmlFor="recording-tab1">
        {isRecording ? elapsed : <Play size={15} color="#6A737D" strokeWidth={1.5} />}
      </label>

      <input
        type="radio"
        name="recording-tab"
        id="recording-tab2"
        className="recording-tab recording-tab--2"
        checked={!isRecording}
        onChange={onPause}
      />
      <label className="recording-tab_label text-[rgb(249,250,251)]" htmlFor="recording-tab2">
        {isRecording ? <Pause size={15} color="#6A737D" strokeWidth={1.5} /> : elapsed}
      </label>

      <button type="button" className="recording-tab_label recording-end-button" onClick={onEnd}>
        <Square size={12.5} color="#6A737D" strokeWidth={2.0} />
      </button>

      <div className="recording-indicator"></div>
    </div>
  );
}
