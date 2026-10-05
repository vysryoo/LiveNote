import { QueryClient } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SessionDetail } from "../api/schemas";
import { sessionKeys } from "../api/sessionApi";
import {
  applyQnaList,
  applySection,
  applyStream,
  applyStreamError,
  applySummary,
  applyTranscript,
} from "./handlers";
import { streamMessageSchema } from "./messages";

const LECTURE_ID = 7;

function baseDetail(): SessionDetail {
  return {
    id: LECTURE_ID,
    userId: 1,
    title: "강의",
    subject: "Physics",
    sttLanguage: "ko",
    status: "RECORDING",
    createdAt: "2026-10-05T10:00:00",
    endAt: null,
    transcripts: [],
    summaries: [
      { id: 1, sectionIndex: 0, startSec: 0, endSec: 30, text: "기존 요약", phase: "final" },
    ],
    resources: [],
    qna: [
      { id: 100, sectionIndex: 0, summaryId: null, type: "concept", question: "q0", answer: "a0" },
      { id: 101, sectionIndex: 1, summaryId: null, type: "concept", question: "q1", answer: "a1" },
    ],
    bookmarks: [],
  };
}

let queryClient: QueryClient;
const detail = () => queryClient.getQueryData<SessionDetail>(sessionKeys.detail(LECTURE_ID))!;

beforeEach(() => {
  queryClient = new QueryClient();
  queryClient.setQueryData(sessionKeys.detail(LECTURE_ID), baseDetail());
});

describe("applySummary", () => {
  it("같은 섹션 요약은 덮어쓰고 id는 유지", () => {
    applySummary(queryClient, LECTURE_ID, { sectionIndex: 0, text: "새 요약", phase: "final" });
    expect(detail().summaries).toEqual([
      { id: 1, sectionIndex: 0, startSec: 0, endSec: 30, text: "새 요약", phase: "final" },
    ]);
  });

  it("새 섹션 요약은 추가", () => {
    applySummary(queryClient, LECTURE_ID, { sectionIndex: 1, text: "다음", phase: "partial" });
    expect(detail().summaries.map((s) => s.sectionIndex)).toEqual([0, 1]);
  });

  it("상세를 받기 전이면 아무것도 하지 않음", () => {
    const empty = new QueryClient();
    applySummary(empty, LECTURE_ID, { sectionIndex: 0, text: "x", phase: null });
    expect(empty.getQueryData(sessionKeys.detail(LECTURE_ID))).toBeUndefined();
  });
});

describe("applyQnaList", () => {
  it("해당 섹션 목록만 교체", () => {
    applyQnaList(queryClient, LECTURE_ID, {
      sectionIndex: 1,
      items: [
        { id: 102, sectionIndex: 1, summaryId: null, type: "advanced", question: "q", answer: "a" },
      ],
    });
    expect(detail().qna.map((q) => q.id)).toEqual([100, 102]);
  });
});

describe("applySection", () => {
  it("현재 섹션 번호를 기록", () => {
    applySection(queryClient, LECTURE_ID, { sectionIndex: 3 });
    expect(queryClient.getQueryData(sessionKeys.currentSection(LECTURE_ID))).toBe(3);
  });
});

describe("applyTranscript", () => {
  it("같은 전사가 다시 오면 추가하지 않음", () => {
    const message = { sectionIndex: 0, startSec: 0, endSec: 5, text: "문장" };
    applyTranscript(queryClient, LECTURE_ID, message);
    applyTranscript(queryClient, LECTURE_ID, message);
    expect(detail().transcripts).toHaveLength(1);
  });
});

describe("applyStream", () => {
  it("토큰은 reducer로 보내고 캐시는 건드리지 않음", () => {
    const dispatch = vi.fn();
    const before = detail();
    applyStream(
      queryClient,
      dispatch,
      LECTURE_ID,
      streamMessageSchema.parse({
        type: "qna_stream",
        cardId: "qna_7_2_3",
        isComplete: false,
        token: "가",
      }),
    );
    expect(dispatch).toHaveBeenCalledWith(
      expect.objectContaining({ type: "STREAM_TOKEN", kind: "qna", sectionIndex: 2, cardIndex: 3 }),
    );
    expect(detail()).toBe(before);
  });

  it("자료 완료 시 카드를 지우고 카드 ID의 섹션 번호로 캐시에 추가", () => {
    const dispatch = vi.fn();
    applyStream(
      queryClient,
      dispatch,
      LECTURE_ID,
      streamMessageSchema.parse({
        type: "resource_stream",
        cardId: "res_7_2_4",
        isComplete: true,
        data: { id: 200, lectureId: 7, type: "PAPER", title: "논문", text: "설명" },
      }),
    );
    expect(dispatch).toHaveBeenCalledWith({ type: "STREAM_COMPLETED", cardId: "res_7_2_4" });
    expect(detail().resources).toEqual([
      expect.objectContaining({ id: 200, sectionIndex: 2, type: "paper", title: "논문" }),
    ]);
  });

  it("이미 있는 QnA는 중복 추가하지 않음", () => {
    applyStream(
      queryClient,
      vi.fn(),
      LECTURE_ID,
      streamMessageSchema.parse({
        type: "qna_stream",
        cardId: "qna_7_1_2",
        isComplete: true,
        data: { id: 101, sectionIndex: 1, type: "concept", question: "q1", answer: "a1" },
      }),
    );
    expect(detail().qna.map((q) => q.id)).toEqual([100, 101]);
  });

  it("완료 데이터 형식이 맞지 않으면 카드만 지우고 캐시는 그대로", () => {
    const dispatch = vi.fn();
    const before = detail();
    applyStream(
      queryClient,
      dispatch,
      LECTURE_ID,
      streamMessageSchema.parse({
        type: "qna_stream",
        cardId: "qna_7_1_2",
        isComplete: true,
        data: {},
      }),
    );
    expect(dispatch).toHaveBeenCalledWith({ type: "STREAM_COMPLETED", cardId: "qna_7_1_2" });
    expect(detail()).toBe(before);
  });
});

describe("applyStreamError", () => {
  it("생성 중 카드 정리를 요청", () => {
    const dispatch = vi.fn();
    applyStreamError(dispatch);
    expect(dispatch).toHaveBeenCalledWith({ type: "STREAMS_FAILED" });
  });
});
