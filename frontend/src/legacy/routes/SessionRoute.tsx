import { useTranslation } from "react-i18next";
import { Navigate, useNavigate, useParams } from "react-router";
import { toast } from "sonner";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { useEndLecture } from "@/features/lectures/hooks/useLectureMutations";
import { SessionPage } from "../components/SessionPage";

export function SessionRoute() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useLogout();
  const endMutation = useEndLecture();
  const lectureId = Number(useParams().lectureId);

  if (!Number.isInteger(lectureId)) return <Navigate to="/lectures" replace />;

  const saveAndEnd = async (title: string) => {
    try {
      await endMutation.mutateAsync({ lectureId, title });
    } catch {
      // EndSessionModal이 에러 메시지를 모달 안에 표시
      throw new Error(t("lectures.endFailed"));
    }
    navigate("/lectures");
    toast.success(t("lectures.toast.ended"));
  };

  // 강의가 바뀌면 SessionPage 내부 상태를 전부 초기화하기 위해 key로 재마운트
  return (
    <SessionPage
      key={lectureId}
      lectureId={lectureId}
      onLogoClick={() => navigate("/lectures")}
      onSettings={() => navigate("/settings")}
      onLogout={logout}
      onSaveAndEnd={saveAndEnd}
    />
  );
}
