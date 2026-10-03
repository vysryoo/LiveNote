import { useNavigate } from "react-router";
import { SettingsPage } from "../components/SettingsPage";
import { useLegacyApp } from "../appContext";

export function SettingsRoute() {
  const navigate = useNavigate();
  const { user, handleSettings } = useLegacyApp();
  if (!user) return null;
  return (
    <SettingsPage
      onBack={() => navigate("/lectures")}
      onSave={handleSettings}
      currentLanguage={user.uiLanguage || "ko"}
    />
  );
}
