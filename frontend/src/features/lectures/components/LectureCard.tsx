import { BookOpen, Clock, MoreVertical } from "lucide-react";
import { useState, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { isLanguageCode, LANGUAGE_LABELS } from "@/shared/i18n";
import { Button } from "@/shared/ui/button";
import { Card } from "@/shared/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import type { Lecture } from "../api/schemas";
import { useRenameLecture } from "../hooks/useLectureMutations";
import { getLectureDurationMinutes, toCategoryLabel } from "../lectureDisplay";

type LectureCardProps = {
  lecture: Lecture;
  onOpen: (lectureId: number) => void;
  onDelete: (lecture: Lecture) => void;
};

export function LectureCard({ lecture, onOpen, onDelete }: LectureCardProps) {
  const { t, i18n } = useTranslation();
  const renameMutation = useRenameLecture();
  const [editingTitle, setEditingTitle] = useState<string | null>(null);
  const isEditing = editingTitle !== null;

  const saveTitle = () => {
    const title = editingTitle?.trim();
    if (!title || renameMutation.isPending) return;
    renameMutation.mutate(
      { lectureId: lecture.id, title },
      {
        onSuccess: () => {
          setEditingTitle(null);
          toast.success(t("lectures.toast.renamed"));
        },
        onError: () => toast.error(t("lectures.toast.renameFailed")),
      },
    );
  };

  const handleCardClick = (e: MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    // 카드 안의 메뉴 버튼이나 제목 입력칸을 누른 경우는 강의로 이동하지 않음
    if (isEditing || target.closest("button, [role=menuitem], input")) return;
    onOpen(lecture.id);
  };

  const durationMinutes = getLectureDurationMinutes(lecture);
  const durationText =
    lecture.status === "RECORDING"
      ? t("lectures.inProgress")
      : durationMinutes === null
        ? "-"
        : durationMinutes >= 60
          ? t("lectures.durationHoursMinutes", {
              hours: Math.floor(durationMinutes / 60),
              minutes: durationMinutes % 60,
            })
          : t("lectures.durationMinutes", { minutes: durationMinutes });

  const createdDate = new Date(lecture.createdAt);
  const dateText = Number.isNaN(createdDate.getTime())
    ? lecture.createdAt
    : createdDate.toLocaleDateString(i18n.language, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });

  const sttLanguage = lecture.sttLanguage;
  const languageText = isLanguageCode(sttLanguage)
    ? LANGUAGE_LABELS[sttLanguage]
    : (sttLanguage ?? "-");

  return (
    <Card
      className="p-6 hover:shadow-lg transition-shadow cursor-pointer relative"
      onClick={handleCardClick}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0 relative">
          <div className="inline-flex items-center gap-2 bg-[#639BEE]/10 text-[#3B72DD] px-3 py-1 rounded-full text-sm mb-3">
            <BookOpen className="w-4 h-4" />
            {toCategoryLabel(lecture.subject) ?? t("lectures.uncategorized")}
          </div>
          {isEditing ? (
            <input
              type="text"
              value={editingTitle}
              onChange={(e) => setEditingTitle(e.target.value)}
              onBlur={saveTitle}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  saveTitle();
                }
                if (e.key === "Escape") setEditingTitle(null);
              }}
              className="text-lg border-b-2 border-[#3B72DD] outline-none w-full bg-white px-2 py-1 rounded"
              autoFocus
            />
          ) : (
            <h3 className="text-lg mb-2">{lecture.title || t("lectures.untitled")}</h3>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setEditingTitle(lecture.title ?? "")}>
              {t("common.edit")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onDelete(lecture)} className="text-destructive">
              {t("common.delete")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="space-y-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4" />
          {dateText} • {durationText}
        </div>
        <div>
          {t("common.language")}: {languageText}
        </div>
      </div>
    </Card>
  );
}
