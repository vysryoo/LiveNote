import React from "react";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { User, Settings, LogOut } from "lucide-react";
import RecordingTabControl from "./RecordingTabControl";
// @ts-ignore - vite에서 이미지 import 지원
import logoImage from "../assets/logo.png";
import type { SessionDetailResponse } from "../services/ports";

interface SessionHeaderProps {
  lecture: SessionDetailResponse | null;
  lectureId: number;
  isRecording: boolean;
  elapsedTime: number;
  isEnded: boolean;
  onToggleRecording: (record: boolean) => void;
  onLogoClickConfirm: () => void;
  onEndConfirm: () => void;
  onSettingsConfirm: () => void;
  onLogoutConfirm: () => void;
}

export function SessionHeader({
  lecture,
  lectureId,
  isRecording,
  elapsedTime,
  isEnded,
  onToggleRecording,
  onLogoClickConfirm,
  onEndConfirm,
  onSettingsConfirm,
  onLogoutConfirm,
}: SessionHeaderProps) {
  return (
    <header className="border-b bg-white shadow-lg">
      <div
        className="px-[3%] py-[0.4%]"
        style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}
      >
        <div className="flex justify-between items-center">
          <button
            onClick={onLogoClickConfirm}
            className="flex items-center hover:opacity-80"
            style={{ gap: "0.8em" }}
          >
            <img
              src={logoImage}
              alt="LiveNote"
              style={{ height: "3em" }}
            />
            <span style={{ fontSize: "1.2em" }}>
              {lecture?.title ?? `세션 ${lectureId}`}
            </span>
          </button>

          <div className="flex items-center" style={{ gap: "1.2em" }}>
            {/* Controls */}
            <div className="flex items-center" style={{ gap: "0.6em" }}>
              <RecordingTabControl
                isRecording={isRecording}
                onToggle={onToggleRecording}
                elapsedTime={elapsedTime}
                onEnd={onEndConfirm}
                isEnded={isEnded}
              />
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-full bg-[#f5f5f5] transition-all duration-300 [box-shadow:2px_2px_4px_#d8d8d8,-2px_-2px_4px_#ffffff] data-[state=open]:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] active:[box-shadow:inset_2px_2px_4px_#d8d8d8,inset_-2px_-2px_4px_#ffffff] hover:bg-[#f5f5f5]"
                  style={{ width: "32px", height: "32px" }}
                >
                  <User
                    style={{ width: "16px", height: "16px" }}
                    color="#6A737D"
                  />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onSettingsConfirm}>
                  <Settings className="w-4 h-4 mr-2" />
                  설정
                </DropdownMenuItem>
                <DropdownMenuItem onClick={onLogoutConfirm}>
                  <LogOut className="w-4 h-4 mr-2" />
                  로그아웃
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </header>
  );
}


