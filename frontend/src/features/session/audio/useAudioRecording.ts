import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { buildTranscriptionSocketUrl } from "../realtime/endpoints";
import { audioSocketMessageSchema } from "../realtime/messages";
import { resampleLinear, toPcm16 } from "./pcm";

// 백엔드가 OpenAI Realtime API에 그대로 전달하는 PCM16 24kHz 형식
const TARGET_SAMPLE_RATE = 24000;
const BUFFER_SIZE = 4096;
const CONNECT_TIMEOUT_MS = 5000;
// 이 시간 동안 음성 전송이 없으면 마이크 입력이 멈춘 것으로 판단
const AUDIO_STALL_MS = 10_000;

export type RecordingFailure = "unsupported" | "micPermissionDenied" | "connectionFailed";
export type RecordingInterruption = "disconnected" | "serverError";

export class RecordingError extends Error {
  constructor(readonly reason: RecordingFailure) {
    super(reason);
    this.name = "RecordingError";
  }
}

type RecordingResources = {
  context: AudioContext;
  processor: ScriptProcessorNode;
  socket: WebSocket;
  stream: MediaStream | null;
  source: MediaStreamAudioSourceNode | null;
};

type UseAudioRecordingOptions = {
  lectureId: number;
  onTranscript: (content: string, isFinal: boolean) => void;
  onInterrupted: (reason: RecordingInterruption, serverMessage?: string) => void;
};

function waitForOpen(socket: WebSocket): Promise<void> {
  if (socket.readyState === WebSocket.OPEN) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => finish(new RecordingError("connectionFailed")),
      CONNECT_TIMEOUT_MS,
    );
    const finish = (error?: Error) => {
      clearTimeout(timer);
      socket.removeEventListener("open", onOpen);
      socket.removeEventListener("error", onFail);
      socket.removeEventListener("close", onFail);
      if (error) reject(error);
      else resolve();
    };
    const onOpen = () => finish();
    const onFail = () => finish(new RecordingError("connectionFailed"));
    socket.addEventListener("open", onOpen);
    socket.addEventListener("error", onFail);
    socket.addEventListener("close", onFail);
  });
}

function toRecordingError(error: unknown): RecordingError {
  if (error instanceof RecordingError) return error;
  if (error instanceof DOMException && error.name === "NotAllowedError") {
    return new RecordingError("micPermissionDenied");
  }
  return new RecordingError("connectionFailed");
}

/**
 * 마이크 음성을 PCM16 24kHz로 변환해 전사 WebSocket으로 보내고 실시간 전사를 받는다.
 *
 * 섹션 번호와 경과 시간은 다루지 않는다. 받은 전사를 어느 섹션에 넣을지는 호출부가 정한다.
 *
 * @param options.lectureId 강의 ID
 * @param options.onTranscript 실시간 전사 수신 시 호출
 * @param options.onInterrupted 녹음 중 연결이 끊기거나 서버가 오류를 보낸 경우 호출. 녹음은 이미 중지된 상태
 * @returns 녹음 상태와 시작·중지 함수. `isAudioActive`는 마이크 입력이 10초 이상 끊기면 `false`
 */
export function useAudioRecording({
  lectureId,
  onTranscript,
  onInterrupted,
}: UseAudioRecordingOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [isAudioActive, setIsAudioActive] = useState(true);
  const resourcesRef = useRef<RecordingResources | null>(null);
  const lastAudioSentAtRef = useRef(0);
  // WebSocket 핸들러는 녹음 시작 시점에 만들어지므로 항상 최신 콜백을 부르도록 ref로 보관
  const callbacksRef = useRef({ onTranscript, onInterrupted });

  useLayoutEffect(() => {
    callbacksRef.current = { onTranscript, onInterrupted };
  });

  const release = () => {
    const resources = resourcesRef.current;
    resourcesRef.current = null;
    if (!resources) return;
    const { context, processor, socket, stream, source } = resources;
    processor.onaudioprocess = null;
    processor.disconnect();
    source?.disconnect();
    stream?.getTracks().forEach((track) => track.stop());
    void context.close().catch(() => undefined);
    socket.onclose = null;
    socket.onmessage = null;
    if (socket.readyState === WebSocket.CONNECTING || socket.readyState === WebSocket.OPEN) {
      socket.close();
    }
  };

  const stop = () => {
    release();
    setIsRecording(false);
  };

  /**
   * 녹음을 시작한다. 이미 녹음 중이면 아무것도 하지 않는다.
   *
   * @throws RecordingError 브라우저가 마이크를 지원하지 않거나, 권한이 거부되거나, 서버에 연결하지 못한 경우
   */
  const start = async () => {
    if (resourcesRef.current) return;
    if (!navigator.mediaDevices?.getUserMedia) throw new RecordingError("unsupported");

    const context = new AudioContext({ sampleRate: TARGET_SAMPLE_RATE });
    const resources: RecordingResources = {
      context,
      processor: context.createScriptProcessor(BUFFER_SIZE, 1, 1),
      socket: new WebSocket(buildTranscriptionSocketUrl(lectureId)),
      stream: null,
      source: null,
    };
    resourcesRef.current = resources;

    try {
      await waitForOpen(resources.socket);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // 연결을 기다리는 사이 stop()이 호출된 경우
      if (resourcesRef.current !== resources) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      resources.stream = stream;
      resources.source = context.createMediaStreamSource(stream);
    } catch (error) {
      if (resourcesRef.current === resources) release();
      throw toRecordingError(error);
    }

    const { processor, socket, source } = resources;
    processor.onaudioprocess = (event) => {
      if (socket.readyState !== WebSocket.OPEN) return;
      const samples = resampleLinear(
        event.inputBuffer.getChannelData(0),
        context.sampleRate,
        TARGET_SAMPLE_RATE,
      );
      socket.send(toPcm16(samples).buffer);
      lastAudioSentAtRef.current = Date.now();
      setIsAudioActive(true);
    };
    socket.onmessage = (event) => {
      let raw: unknown;
      try {
        raw = JSON.parse(String(event.data));
      } catch {
        return;
      }
      const parsed = audioSocketMessageSchema.safeParse(raw);
      if (!parsed.success) return;
      if (parsed.data.type === "transcript") {
        const { content, isFinal } = parsed.data.data;
        if (content) callbacksRef.current.onTranscript(content, isFinal);
        return;
      }
      stop();
      callbacksRef.current.onInterrupted("serverError", parsed.data.data.error ?? undefined);
    };
    socket.onclose = () => {
      stop();
      callbacksRef.current.onInterrupted("disconnected");
    };

    processor.connect(context.destination);
    source?.connect(processor);
    lastAudioSentAtRef.current = Date.now();
    setIsAudioActive(true);
    setIsRecording(true);
  };

  useEffect(() => {
    if (!isRecording) return;
    const timer = setInterval(() => {
      if (Date.now() - lastAudioSentAtRef.current > AUDIO_STALL_MS) setIsAudioActive(false);
    }, 1000);
    return () => clearInterval(timer);
  }, [isRecording]);

  useEffect(() => () => release(), []);

  return { isRecording, isAudioActive, start, stop };
}
