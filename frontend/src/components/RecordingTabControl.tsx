import './RecordingTabControl.css';
import { useEffect, useState } from 'react';
import { Play, Pause, Square } from 'lucide-react';

interface RecordingTabControlProps {
  isRecording: boolean;
  onToggle: (recording: boolean) => void;
  elapsedTime: number; // in seconds
  onEnd: () => void;
  isEnded?: boolean;
}

export default function RecordingTabControl({
  isRecording,
  onToggle,
  elapsedTime,
  onEnd,
  isEnded = false
}: RecordingTabControlProps) {
  const [currentTime, setCurrentTime] = useState(elapsedTime);

  useEffect(() => {
    setCurrentTime(elapsedTime);
  }, [elapsedTime]);

  useEffect(() => {
    if (isRecording) {
      const interval = setInterval(() => {
        setCurrentTime(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isRecording]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="recording-tab-container">
      <input
        type="radio"
        name="recording-tab"
        id="recording-tab1"
        className="recording-tab recording-tab--1"
        checked={isRecording && !isEnded}
        onChange={() => !isEnded && onToggle(true)}
        disabled={isEnded}
      />
      <label className="recording-tab_label" htmlFor="recording-tab1">
        {isEnded ? (
          <Play className="w-4 h-4" color="#6A737D" />
        ) : isRecording ? (
          <span style={{ color: '#6A737D' }}>{formatTime(currentTime)}</span>
        ) : (
          <Play size={15} color="#6A737D" strokeWidth={1.5} />
        )}
      </label>

      <input
        type="radio"
        name="recording-tab"
        id="recording-tab2"
        className="recording-tab recording-tab--2"
        checked={!isRecording && !isEnded}
        onChange={() => !isEnded && onToggle(false)}
        disabled={isEnded}
      />
      <label className="recording-tab_label text-[rgb(249,250,251)]" htmlFor="recording-tab2">
        {isEnded ? (
          <Pause size={15} color="#6A737D" strokeWidth={1.5} />
        ) : !isRecording ? (
          <span style={{ color: '#6A737D' }}>{formatTime(currentTime)}</span>
        ) : (
          <Pause size={15} color="#6A737D" strokeWidth={1.5} />
        )}
      </label>

      <button
        type="button"
        className="recording-tab_label recording-end-button"
        onClick={onEnd}
        disabled={isEnded}
      >
        {isEnded ? (
          <span style={{ color: '#6A737D' }}>{formatTime(currentTime)}</span>
        ) : (
          <Square size={12.5} color="#6A737D" strokeWidth={2.0} />
        )}
      </button>

      <div className="recording-indicator"></div>
    </div>
  );
}