import { useNavigate } from "react-router";
import { MainPage } from "../components/MainPage";
import { useLegacyApp } from "../appContext";

export function MainRoute() {
  const navigate = useNavigate();
  const app = useLegacyApp();
  return (
    <MainPage
      onNewLecture={app.openNewLectureModal}
      onSessionClick={(sessionId) => navigate(`/lectures/${sessionId}`)}
      onSettings={() => navigate("/settings")}
      onLogout={app.handleLogout}
      onDeleteSession={app.handleDeleteSession}
      onRenameSession={app.handleRenameSession}
      lectures={app.lectures}
      loading={app.lecturesLoading}
    />
  );
}
