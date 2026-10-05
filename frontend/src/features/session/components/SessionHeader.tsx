import { LogOut, Settings, User } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import logoImage from "@/assets/logo.png";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

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
  const { t } = useTranslation();
  return (
    <header className="border-b bg-white shadow-lg">
      <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={onLogoClick}
            className="flex items-center hover:opacity-80"
            style={{ gap: "0.8em" }}
          >
            <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
            <span style={{ fontSize: "1.2em" }}>{title}</span>
          </button>

          <div className="flex items-center" style={{ gap: "1.2em" }}>
            <div className="flex items-center" style={{ gap: "0.6em" }}>
              {recordingControl}
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-full bg-[#f5f5f5] transition-all duration-300 [box-shadow:2px_2px_4px_#d8d8d8,-2px_-2px_4px_#ffffff] data-[state=open]:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] active:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] hover:bg-[#f5f5f5]"
                  style={{ width: "32px", height: "32px" }}
                >
                  <User style={{ width: "16px", height: "16px" }} color="#6A737D" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onSettingsClick}>
                  <Settings className="w-4 h-4 mr-2" />
                  {t("common.settings")}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onLogoutClick}>
                  <LogOut className="w-4 h-4 mr-2" />
                  {t("common.logout")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  );
}
