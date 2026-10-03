import { Navigate, useNavigate, useParams } from "react-router";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { SessionPage } from "../components/SessionPage";
import { useLegacyApp } from "../appContext";

export function SessionRoute() {
  const navigate = useNavigate();
  const { handleEndSession } = useLegacyApp();
  const logout = useLogout();
  const lectureId = Number(useParams().lectureId);

  if (!Number.isInteger(lectureId)) return <Navigate to="/lectures" replace />;

  // 강의가 바뀌면 SessionPage 내부 상태를 전부 초기화하기 위해 key로 재마운트
  return (
    <SessionPage
      key={lectureId}
      lectureId={lectureId}
      onLogoClick={() => navigate("/lectures")}
      onSettings={() => navigate("/settings")}
      onLogout={logout}
      onSaveAndEnd={(sessionName) => handleEndSession(lectureId, sessionName)}
    />
  );
}
