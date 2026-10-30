import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { useEndLecture } from "@/features/lectures/hooks/useLectureMutations";

// 세션을 떠나는 동작은 모두 종료 대화창을 거친 뒤 실행
export type LeaveAction = "end" | "home" | "settings" | "logout";

/**
 * 세션 화면을 떠나는 흐름을 관리한다. 떠나기를 요청하면 녹음을 멈추고 종료 대화창을 연다.
 * 대화창에서 저장하면 강의를 종료한 뒤 요청한 곳으로 이동한다.
 *
 * @param lectureId 강의 ID
 * @param stopRecording 녹음 중지 함수
 * @returns 대화창 열림 여부와 요청·취소·저장 함수. `saveAndEnd`는 종료 요청이 실패하면 예외를 던짐
 */
export function useLeaveSession(lectureId: number, stopRecording: () => void) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useLogout();
  const endMutation = useEndLecture();
  const [leaveAction, setLeaveAction] = useState<LeaveAction | null>(null);

  return {
    isConfirming: leaveAction !== null,
    request: (action: LeaveAction) => {
      stopRecording();
      setLeaveAction(action);
    },
    cancel: () => setLeaveAction(null),
    saveAndEnd: async (title: string) => {
      await endMutation.mutateAsync({ lectureId, title });
      const action = leaveAction;
      setLeaveAction(null);
      toast.success(t("lectures.toast.ended"));
      if (action === "settings") navigate("/settings");
      else if (action === "logout") logout();
      else navigate("/lectures");
    },
  };
}
