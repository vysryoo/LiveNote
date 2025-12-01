import { useCallback, useEffect, useRef, useState } from "react";
import type { BackendPort } from "../services/ports";

interface UseRecordingParams {
  lectureId: number;
  backend: BackendPort;
  t: (key: string) => string;
  onLiveTranscript: (sectionIndex: number, text: string, isFinal: boolean) => void;
  onRecordingStartedOnce: () => void;
  serverSectionIndex?: number;
}

interface UseRecordingResult {
  isRecording: boolean;
  isEnded: boolean;
  elapsedTime: number;
  currentSectionIndex: number;
  hasRecordingStarted: boolean;
  handleToggleRecording: (shouldRecord: boolean) => Promise<void>;
}

const DEV_AUDIO_URL = (import.meta as any).env?.VITE_DEV_AUDIO_URL as string | undefined;
const DISABLE_DEV_AUDIO = ((import.meta as any).env?.VITE_DISABLE_DEV_AUDIO as string | undefined)?.trim() === 'true';

export function useRecording({
  lectureId,
  backend,
  t,
  onLiveTranscript,
  onRecordingStartedOnce,
  serverSectionIndex,
}: UseRecordingParams): UseRecordingResult {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isEnded, setIsEnded] = useState(false);
  const [hasRecordingStarted, setHasRecordingStarted] = useState(false);
  const [isAudioActive, setIsAudioActive] = useState(true);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceNodeRef = useRef<AudioNode | null>(null);
  const devAudioEndedRef = useRef(false);
  const elapsedTimeRef = useRef(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const lastAudioSentRef = useRef<number | null>(null);
  const currentSectionIndexRef = useRef(0);

  const stopSourceNode = useCallback(() => {
    if (sourceNodeRef.current) {
      try {
        const node = sourceNodeRef.current as AudioBufferSourceNode;
        if (typeof node.stop === "function") {
          try {
            node.stop();
          } catch (err) {
            console.debug("[DEV_AUDIO] AudioBufferSourceNode stop error", err);
          }
        }
      } catch (err) {
        console.debug("Audio node disconnect error", err);
      }
      try {
        sourceNodeRef.current.disconnect();
      } catch {
        // ignore
      }
      sourceNodeRef.current = null;
    }
  }, []);

  const handleToggleRecording = useCallback(
    async (shouldRecord: boolean) => {
      if (shouldRecord) {
        setIsEnded(false);
        if (!hasRecordingStarted) {
          setHasRecordingStarted(true);
          onRecordingStartedOnce();
        }
        lastAudioSentRef.current = Date.now();
        setIsAudioActive(true);

        try {
          if (DEV_AUDIO_URL && !DISABLE_DEV_AUDIO) {
            console.info(`[DEV_AUDIO] Using file playback: ${DEV_AUDIO_URL}`);
          } else {
            console.info("[DEV_AUDIO] Disabled or no DEV_AUDIO_URL — using microphone flow");
          }
          devAudioEndedRef.current = false;

          const AudioContextClass =
            window.AudioContext || (window as any).webkitAudioContext;
          const targetSampleRate = 24000;
          const audioContext = new AudioContextClass({
            sampleRate: targetSampleRate,
          });
          audioContextRef.current = audioContext;

          const actualSampleRate = audioContext.sampleRate;
          const needsResampling =
            Math.abs(actualSampleRate - targetSampleRate) > 100;

          const bufferSize = 4096;
          const scriptProcessor = audioContext.createScriptProcessor(
            bufferSize,
            1,
            1
          );
          scriptProcessorRef.current = scriptProcessor;

          scriptProcessor.onaudioprocess = (event) => {
            if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
              return;
            }

            const inputBuffer = event.inputBuffer;
            let inputData = inputBuffer.getChannelData(0);

            if (needsResampling) {
              const ratio = targetSampleRate / actualSampleRate;
              const outputLength = Math.round(inputData.length * ratio);
              const resampledData = new Float32Array(outputLength);

              for (let i = 0; i < outputLength; i++) {
                const srcIndex = i / ratio;
                const srcIndexFloor = Math.floor(srcIndex);
                const srcIndexCeil = Math.min(
                  srcIndexFloor + 1,
                  inputData.length - 1
                );
                const fraction = srcIndex - srcIndexFloor;

                resampledData[i] =
                  inputData[srcIndexFloor] * (1 - fraction) +
                  inputData[srcIndexCeil] * fraction;
              }
              inputData = resampledData;
            }

            const pcm16Data = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
              const sample = Math.max(-1, Math.min(1, inputData[i]));
              pcm16Data[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
            }

            backend.lecture.sendAudioData(wsRef.current, pcm16Data.buffer);
            lastAudioSentRef.current = Date.now();
            setIsAudioActive(true);
          };

          // DEV audio fetch/decoding is handled below in `bufferSourcePromise`.
          const bufferSourcePromise = DEV_AUDIO_URL
            ? (async () => {
                const response = await fetch(DEV_AUDIO_URL);
                if (!response.ok) {
                  throw new Error(`DEV_AUDIO 파일 로드 실패: ${response.statusText}`);
                }
                const fileBuffer = await response.arrayBuffer();
                const decodedBuffer = await new Promise<AudioBuffer>(
                  (resolve, reject) => {
                    audioContext.decodeAudioData(
                      fileBuffer.slice(0),
                      (buffer) => resolve(buffer),
                      (error) => reject(error)
                    );
                  }
                );
                const bufferSource = audioContext.createBufferSource();
                bufferSource.buffer = decodedBuffer;
                bufferSource.onended = () => {
                  devAudioEndedRef.current = true;
                  console.info("[DEV_AUDIO] Playback finished");
                  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                    wsRef.current.close(1000, "dev-audio-finished");
                  }
                };
                return bufferSource as AudioNode;
              })()
            : Promise.resolve(null as AudioNode | null);

          // Ensure websocket is created for either flow
          const ws =
            wsRef.current && wsRef.current.readyState === WebSocket.OPEN
              ? wsRef.current
              : backend.lecture.connectTranscription(lectureId);
          wsRef.current = ws;

          if (ws.readyState === WebSocket.CONNECTING) {
            await new Promise<void>((resolve, reject) => {
              const timeout = setTimeout(() => {
                reject(new Error("WebSocket connection timeout"));
              }, 5000);

              const onOpen = () => {
                clearTimeout(timeout);
                ws.removeEventListener("open", onOpen);
                ws.removeEventListener("error", onError);
                resolve();
              };

              const onError = (event: Event) => {
                clearTimeout(timeout);
                ws.removeEventListener("open", onOpen);
                ws.removeEventListener("error", onError);
                console.error("Transcription websocket connection error", event);
                reject(new Error("WebSocket connection failed"));
              };

              ws.addEventListener("open", onOpen);
              ws.addEventListener("error", onError);
            });
          }

          const maybeBufferSource = await bufferSourcePromise;

          if (maybeBufferSource) {
            // DEV audio playback flow
            sourceNodeRef.current = maybeBufferSource;
            scriptProcessor.connect(audioContext.destination);
            maybeBufferSource.connect(scriptProcessor);
            if (maybeBufferSource instanceof AudioBufferSourceNode) {
              (maybeBufferSource as AudioBufferSourceNode).start();
            }
          } else {
            // Microphone flow: fallback to real mic input
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
              throw new Error("브라우저가 마이크 사용을 지원하지 않습니다.");
            }
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioStreamRef.current = stream;
            const mediaSource = audioContext.createMediaStreamSource(stream);
            sourceNodeRef.current = mediaSource;
            scriptProcessor.connect(audioContext.destination);
            mediaSource.connect(scriptProcessor as any);
          }

          ws.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);
              if (message.type === "transcript" && message.data) {
                const content = message.data.content;
                const isFinal = message.data.isFinal || false;
                if (content) {
                  console.log(
                    `📝 실시간 전사 수신: isFinal=${isFinal}, content="${content.substring(
                      0,
                      50
                    )}..."`
                  );
                  const sectionIndex = Math.max(currentSectionIndexRef.current, 0);
                  onLiveTranscript(sectionIndex, content, isFinal);
                }
              } else if (message.type === "error" && message.data) {
                console.error("WebSocket error:", message.data.error);
                alert(message.data.error || t("session.wsError"));
              }
            } catch (err) {
              console.error("WebSocket message parse error", err);
            }
          };

          ws.onclose = () => {
            wsRef.current = null;
            setIsRecording(false);
            if (audioStreamRef.current) {
              audioStreamRef.current.getTracks().forEach((track) => track.stop());
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
          };

          ws.onerror = (event) => {
            console.error("Transcription websocket error", event);
            alert(t("session.wsError"));
            setIsRecording(false);
          };

          setIsRecording(true);
        } catch (error) {
          console.error("Failed to start recording", error);
          alert(
            error instanceof Error && error.name === "NotAllowedError"
              ? t("session.micPermissionDenied")
              : t("session.recordingError")
          );

          if (audioStreamRef.current) {
            audioStreamRef.current.getTracks().forEach((track) => track.stop());
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
        setIsRecording(false);

        if (scriptProcessorRef.current) {
          scriptProcessorRef.current.disconnect();
          scriptProcessorRef.current = null;
        }
        stopSourceNode();
        if (audioContextRef.current) {
          audioContextRef.current.close().catch(console.error);
          audioContextRef.current = null;
        }

        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop());
          audioStreamRef.current = null;
        }

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
    [backend, hasRecordingStarted, lectureId, onLiveTranscript, onRecordingStartedOnce, stopSourceNode, t]
  );

  useEffect(() => {
    if (!isRecording || !isAudioActive) return;
    const timer = window.setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, [isRecording, isAudioActive]);

  useEffect(() => {
    elapsedTimeRef.current = elapsedTime;
  }, [elapsedTime]);

  useEffect(() => {
    if (serverSectionIndex != null) {
      currentSectionIndexRef.current = serverSectionIndex;
      setCurrentSectionIndex(serverSectionIndex);
      const targetElapsed = serverSectionIndex * 30;
      if (elapsedTime < targetElapsed) {
        setElapsedTime(targetElapsed);
      }
    }
  }, [serverSectionIndex]);

  useEffect(() => {
    if (!isRecording) {
      currentSectionIndexRef.current = 0;
      setCurrentSectionIndex(0);
      return;
    }
    const localSection = Math.floor(elapsedTime / 30);
    const effectiveSection =
      serverSectionIndex != null
        ? Math.min(localSection, serverSectionIndex)
        : localSection;
    if (effectiveSection !== currentSectionIndexRef.current) {
      currentSectionIndexRef.current = effectiveSection;
      setCurrentSectionIndex(effectiveSection);
    }
  }, [elapsedTime, isRecording, serverSectionIndex]);

  useEffect(() => {
    const checker = setInterval(() => {
      if (!isRecording) return;
      const last = lastAudioSentRef.current;
      if (last == null) return;
      if (Date.now() - last > 10000 && isAudioActive) {
        setIsAudioActive(false);
      }
    }, 1000);
    return () => clearInterval(checker);
  }, [isRecording, isAudioActive]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        try {
          if (mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.stop();
          }
        } catch (error) {
          console.error("Failed to stop MediaRecorder on cleanup", error);
        }
        mediaRecorderRef.current = null;
      }

      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop());
        audioStreamRef.current = null;
      }

      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (error) {
          console.error(
            "Failed to close transcription websocket on cleanup",
            error
          );
        }
        wsRef.current = null;
      }
    };
  }, []);

  return {
    isRecording,
    isEnded,
    elapsedTime,
    currentSectionIndex,
    hasRecordingStarted,
    handleToggleRecording,
  };
}
