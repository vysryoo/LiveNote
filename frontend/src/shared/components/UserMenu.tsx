import { LogOut, Settings, User } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";

type UserMenuProps = {
  onSettingsClick: () => void;
  onLogoutClick: () => void;
};

/**
 * 헤더 오른쪽의 사용자 메뉴(설정, 로그아웃)를 표시한다.
 *
 * @param props.onSettingsClick 설정 선택 시 호출
 * @param props.onLogoutClick 로그아웃 선택 시 호출
 */
export function UserMenu({ onSettingsClick, onLogoutClick }: UserMenuProps) {
  const { t } = useTranslation();
  return (
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
  );
}
