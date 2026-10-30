import type { ReactNode } from "react";
import { AppHeader, AppLogo } from "@/shared/components/AppHeader";
import { UserMenu } from "@/shared/components/UserMenu";

type SessionHeaderProps = {
  title: string;
  recordingControl: ReactNode;
  onLogoClick: () => void;
  onSettingsClick: () => void;
  onLogoutClick: () => void;
};

export function SessionHeader({
  title,
  recordingControl,
  onLogoClick,
  onSettingsClick,
  onLogoutClick,
}: SessionHeaderProps) {
  return (
    <AppHeader opaque>
      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={onLogoClick}
          className="flex items-center hover:opacity-80"
          style={{ gap: "0.8em" }}
        >
          <AppLogo />
          <span style={{ fontSize: "1.2em" }}>{title}</span>
        </button>

        <div className="flex items-center" style={{ gap: "1.2em" }}>
          <div className="flex items-center" style={{ gap: "0.6em" }}>
            {recordingControl}
          </div>
          <UserMenu onSettingsClick={onSettingsClick} onLogoutClick={onLogoutClick} />
        </div>
      </div>
    </AppHeader>
  );
}
