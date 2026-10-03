import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import { User, Settings, LogOut, Plus, MoreVertical, BookOpen, Clock, Loader2 } from "lucide-react";
import { useMemo, useState } from "react";
import logoImage from "figma:asset/logo.png";
import type { Lecture } from "../services/ports";
import { useI18n } from "../i18n/I18nContext";

interface MainPageProps {
  onNewLecture: () => void;
  onSessionClick: (lectureId: number) => void;
  onSettings: () => void;
  onLogout: () => void;
  onDeleteSession: (lectureId: number) => void;
  onRenameSession: (lectureId: number, newName: string) => void;
  lectures: Lecture[];
  loading?: boolean;
}

function formatLectureDuration(duration: number | null | undefined, status: Lecture["status"]) {
  if (status === "recording") return "진행 중";
  if (duration == null) return "-";
  const mins = Math.floor(duration / 60);
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  if (hrs > 0) {
    return `${hrs}시간 ${remMins}분`;
  }
  return `${remMins}분`;
}

function formatLectureDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit" });
}

export function MainPage({
  onNewLecture,
  onSessionClick,
  onSettings,
  onLogout,
  onDeleteSession,
  onRenameSession,
  lectures,
  loading = false,
}: MainPageProps) {
  const { t, language } = useI18n();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");

  const handleRename = async (lectureId: number) => {
    const trimmed = editName.trim();
    if (!trimmed) {
      return;
    }
    try {
      await onRenameSession(lectureId, trimmed);
      setEditingId(null);
      setEditName("");
    } catch (error) {
      console.error(error);
    }
  };

  const startEdit = (lecture: Lecture) => {
    setEditingId(lecture.id);
    setEditName(lecture.title ?? "");
  };

  const orderedLectures = useMemo(
    () =>
      [...lectures].sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
      ),
    [lectures],
  );

  return (
    <div className="min-h-screen bg-background bg-wave-pattern-bottom">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
            </div>

            <div className="flex items-center" style={{ gap: "1.2em" }}>
              <Button onClick={onNewLecture} className="bg-[#3B72DD] hover:bg-[#4D82E0]">
                <Plus style={{ width: "1.4em", height: "1.4em", marginRight: "0.5em" }} />
                {t("main.startNewLecture")}
              </Button>

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
                  <DropdownMenuItem onClick={onSettings}>
                    <Settings className="w-4 h-4 mr-2" />
                    {t("common.settings")}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={onLogout}>
                    <LogOut className="w-4 h-4 mr-2" />
                    {t("common.logout")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl mb-2">{t("main.myLectures")}</h1>
            <p className="text-muted-foreground">
              {(() => {
                const n = lectures.length;
                switch (language) {
                  case "English":
                    return n === 1
                      ? `So far you’ve run ${n} lecture`
                      : `So far you’ve run ${n} lectures`;
                  case "日本語":
                    return `これまでに ${n} 件の講義を実施しました`;
                  case "汉语":
                    return `到目前为止已进行 ${n} 次课程`;
                  default:
                    return `지금까지 ${n}개의 강의를 진행했습니다`;
                }
              })()}
            </p>
          </div>
        </div>

        {/* Sessions Grid */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : orderedLectures.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-xl mb-2">{t("main.noLecturesTitle")}</h3>
            <p className="text-muted-foreground mb-6">{t("main.noLecturesDesc")}</p>
            <Button onClick={onNewLecture} className="bg-[#3B72DD] hover:bg-[#4D82E0]">
              <Plus className="w-5 h-5 mr-2" />
              {t("main.startNewLecture")}
            </Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {orderedLectures.map((lecture) => (
              <Card
                key={lecture.id}
                className="p-6 hover:shadow-lg transition-shadow cursor-pointer relative"
                onClick={(e) => {
                  // Don't navigate if clicking on dropdown or editing
                  const target = e.target as HTMLElement;
                  if (
                    target.closest("button") ||
                    target.closest('[role="menuitem"]') ||
                    target.tagName === "INPUT" ||
                    editingId === lecture.id
                  ) {
                    return;
                  }
                  onSessionClick(lecture.id);
                }}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 min-w-0 relative">
                    <div className="inline-flex items-center gap-2 bg-[#639BEE]/10 text-[#3B72DD] px-3 py-1 rounded-full text-sm mb-3">
                      <BookOpen className="w-4 h-4" />
                      {lecture.subject || "기타"}
                    </div>
                    {editingId === lecture.id ? (
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onBlur={() => {
                          void handleRename(lecture.id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            void handleRename(lecture.id);
                          }
                          if (e.key === "Escape") {
                            setEditingId(null);
                            setEditName("");
                          }
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="text-lg border-b-2 border-[#3B72DD] outline-none w-full bg-white px-2 py-1 rounded"
                        autoFocus
                      />
                    ) : (
                      <h3 className="text-lg mb-2">{lecture.title || "제목 없음"}</h3>
                    )}
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          startEdit(lecture);
                        }}
                      >
                        {t("common.edit")}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(lecture.id);
                        }}
                        className="text-destructive"
                      >
                        {t("common.delete")}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    {formatLectureDate(lecture.createdAt)} •{" "}
                    {formatLectureDuration(lecture.duration, lecture.status)}
                  </div>
                  <div>언어: {lecture.sttLanguage || "-"}</div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
