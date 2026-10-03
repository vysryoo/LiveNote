import { useNavigate } from "react-router";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { MainPage } from "../components/MainPage";
import { useLegacyApp } from "../appContext";

export function MainRoute() {
  const navigate = useNavigate();
  const app = useLegacyApp();
  const logout = useLogout();
  return (
    <MainPage
      onNewLecture={app.openNewLectureModal}
      onSessionClick={(sessionId) => navigate(`/lectures/${sessionId}`)}
      onSettings={() => navigate("/settings")}
      onLogout={logout}
      onDeleteSession={app.handleDeleteSession}
      onRenameSession={app.handleRenameSession}
      lectures={app.lectures}
      loading={app.lecturesLoading}
    />
  );
}
