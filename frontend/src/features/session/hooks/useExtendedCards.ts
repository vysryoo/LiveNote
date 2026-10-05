import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { startCardStream } from "../api/sessionApi";
import { sessionDetailQuery } from "./useSessionDetail";

const QNA_TYPES = ["concept", "application", "advanced", "comparison"];
const RESOURCE_TYPES = ["paper", "wiki", "video", "blog"];
// 백엔드 AI 서버가 요약 직후 기본으로 만드는 카드가 0, 1번이라 추가 카드는 2번부터
const FIRST_EXTENDED_CARD_INDEX = 2;
// 이보다 많이 생성된 섹션은 이미 추가 요청을 한 것으로 보고 다시 요청하지 않음 (API 사용량 제한)
const MAX_DEFAULT_CARDS = 2;

/**
 * 분할 화면을 열 때 호출해 섹션의 QnA 4종과 자료 4종을 추가로 생성하도록 요청하는 함수를 반환한다.
 *
 * 호출할 때마다 강의 상세를 새로 받아 캐시를 갱신한다. 추가 생성은 확정 요약이 있고 기본 카드만 생성된 섹션에 한해,
 * 화면을 연 동안 섹션당 한 번만 요청한다.
 *
 * @param lectureId 강의 ID
 * @returns 요청 함수와, 요청을 보내는 중인 섹션 번호
 */
export function useExtendedCards(lectureId: number) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();
  const requestedSectionsRef = useRef(new Set<number>());

  const mutation = useMutation({
    mutationFn: async (sectionIndex: number) => {
      // 분할 화면을 열 때마다 최신 카드를 보여 주고, 추가 요청 여부도 최신 서버 상태로 판단하기 위해 새로 받음
      const detail = await queryClient.fetchQuery({
        ...sessionDetailQuery(lectureId),
        staleTime: 0,
      });
      const summary = detail.summaries.find((s) => s.sectionIndex === sectionIndex);
      const qnaCount = detail.qna.filter((q) => q.sectionIndex === sectionIndex).length;
      const resourceCount = detail.resources.filter((r) => r.sectionIndex === sectionIndex).length;
      if (summary?.phase !== "final") return;
      if (qnaCount > MAX_DEFAULT_CARDS || resourceCount > MAX_DEFAULT_CARDS) return;
      if (requestedSectionsRef.current.has(sectionIndex)) return;
      requestedSectionsRef.current.add(sectionIndex);

      const requests = [
        ...QNA_TYPES.map((subtype, i) => ({ kind: "qna" as const, subtype, i })),
        ...RESOURCE_TYPES.map((subtype, i) => ({ kind: "resource" as const, subtype, i })),
      ].map(({ kind, subtype, i }) =>
        startCardStream({
          lectureId,
          sectionIndex,
          cardIndex: FIRST_EXTENDED_CARD_INDEX + i,
          kind,
          subtype,
        }),
      );
      const results = await Promise.allSettled(requests);
      if (results.some((result) => result.status === "rejected")) {
        toast.error(t("session.streamFailed"));
      }
    },
  });

  return {
    request: (sectionIndex: number) => mutation.mutate(sectionIndex),
    pendingSectionIndex: mutation.isPending ? mutation.variables : null,
  };
}
