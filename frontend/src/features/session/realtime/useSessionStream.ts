import { Client, type IMessage } from "@stomp/stompjs";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useEffectEvent } from "react";
import type { z } from "zod";
import { getFreshAuthToken } from "@/shared/lib/http";
import { sessionKeys } from "../api/sessionApi";
import type { SessionAction } from "../state/sessionReducer";
import { STOMP_BROKER_URL } from "./endpoints";
import {
  applyQnaList,
  applyResourceList,
  applySection,
  applyStream,
  applyStreamError,
  applySummary,
  applyTranscript,
} from "./handlers";
import {
  errorMessageSchema,
  qnaListMessageSchema,
  resourceListMessageSchema,
  sectionMessageSchema,
  streamMessageSchema,
  summaryMessageSchema,
  transcriptMessageSchema,
} from "./messages";

function parseMessage<T extends z.ZodType>(
  schema: T,
  topic: string,
  message: IMessage,
): z.infer<T> | null {
  let raw: unknown;
  try {
    raw = JSON.parse(message.body);
  } catch {
    raw = undefined;
  }
  const result = schema.safeParse(raw);
  if (result.success) return result.data;
  // 실제 메시지 형식을 확인하기 위한 로그. 스키마가 실제 메시지와 다를 때 원인 추적에 사용
  // eslint-disable-next-line no-console
  console.warn(`[session] ${topic} 메시지 형식이 예상과 다름`, message.body, result.error);
  return null;
}

type UseSessionStreamOptions = {
  lectureId: number;
  dispatch: (action: SessionAction) => void;
  onStreamError: () => void;
};

/**
 * 강의의 STOMP 토픽을 구독하고 메시지를 Query 캐시와 세션 reducer에 반영한다.
 *
 * 연결은 `lectureId`가 바뀔 때만 다시 맺는다. 처리 함수는 Query 캐시와 dispatch만 사용해 화면 상태를 붙잡지 않는다.
 * 연결(재연결 포함)될 때마다 강의 상세를 다시 받아, 연결이 없던 동안의 변경을 반영한다.
 *
 * @param options.lectureId 강의 ID
 * @param options.dispatch 세션 reducer의 dispatch
 * @param options.onStreamError `/error` 메시지를 받았을 때 호출. 사용자 안내에 사용
 */
export function useSessionStream({ lectureId, dispatch, onStreamError }: UseSessionStreamOptions) {
  const queryClient = useQueryClient();
  const notifyStreamError = useEffectEvent(onStreamError);

  useEffect(() => {
    // RabbitMQ STOMP는 /topic/ 뒤에 '/'를 허용하지 않아 '.'으로 구분함
    const topic = (name: string) => `/topic/lectures.${lectureId}.${name}`;
    const client = new Client({
      brokerURL: STOMP_BROKER_URL,
      reconnectDelay: 5000,
      heartbeatIncoming: 4000,
      heartbeatOutgoing: 4000,
    });
    // 재연결 때도 그 시점의 토큰을 쓰도록 연결 직전에 헤더를 채움. 만료가 임박했으면 먼저 갱신
    client.beforeConnect = async () => {
      const token = await getFreshAuthToken();
      client.connectHeaders = token ? { Authorization: `Bearer ${token}` } : {};
    };

    client.onConnect = () => {
      const subscribe = <T extends z.ZodType>(
        name: string,
        schema: T,
        handle: (message: z.infer<T>) => void,
      ) => {
        client.subscribe(topic(name), (frame) => {
          const message = parseMessage(schema, name, frame);
          if (message) handle(message);
        });
      };

      subscribe("summary", summaryMessageSchema, (m) => applySummary(queryClient, lectureId, m));
      subscribe("qna", qnaListMessageSchema, (m) => applyQnaList(queryClient, lectureId, m));
      subscribe("resources", resourceListMessageSchema, (m) =>
        applyResourceList(queryClient, lectureId, m),
      );
      subscribe("section", sectionMessageSchema, (m) => applySection(queryClient, lectureId, m));
      subscribe("transcripts", transcriptMessageSchema, (m) =>
        applyTranscript(queryClient, lectureId, m),
      );
      subscribe("stream", streamMessageSchema, (m) =>
        applyStream(queryClient, dispatch, lectureId, m),
      );
      subscribe("error", errorMessageSchema, () => {
        applyStreamError(dispatch);
        notifyStreamError();
      });
      // 첫 연결 전이나 끊긴 동안 놓친 메시지를 보충하기 위해 구독 직후 상세를 다시 받음
      void queryClient.invalidateQueries({ queryKey: sessionKeys.detail(lectureId) });
    };

    client.activate();
    return () => {
      void client.deactivate();
    };
  }, [lectureId, queryClient, dispatch]);
}
