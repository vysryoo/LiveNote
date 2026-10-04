import { Loader2, LogOut, Plus, Settings, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import logoImage from "@/assets/logo.png";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { Button } from "@/shared/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/shared/ui/dropdown-menu";
import type { Lecture } from "../api/schemas";
import { useLectureList } from "../hooks/useLectureList";
import { useDeleteLecture } from "../hooks/useLectureMutations";
import { DeleteLectureDialog } from "./DeleteLectureDialog";
import { LectureCard } from "./LectureCard";
import { NewLectureDialog } from "./NewLectureDialog";

export function LectureListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useLogout();
  const lectureList = useLectureList();
  const deleteMutation = useDeleteLecture();
  const [newLectureOpen, setNewLectureOpen] = useState(false);
  const [lectureToDelete, setLectureToDelete] = useState<Lecture | null>(null);

  const lectures = lectureList.data ?? [];
  const openNewLecture = () => setNewLectureOpen(true);

  const confirmDelete = () => {
    if (!lectureToDelete) return;
    deleteMutation.mutate(lectureToDelete.id, {
      onSuccess: () => toast.success(t("lectures.toast.deleted")),
      onError: () => toast.error(t("lectures.toast.deleteFailed")),
    });
    setLectureToDelete(null);
  };

  return (
    <div className="min-h-screen bg-background bg-wave-pattern-bottom">
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
            </div>

            <div className="flex items-center" style={{ gap: "1.2em" }}>
              <Button onClick={openNewLecture} className="bg-[#3B72DD] hover:bg-[#4D82E0]">
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
                  <DropdownMenuItem onClick={() => navigate("/settings")}>
                    <Settings className="w-4 h-4 mr-2" />
                    {t("common.settings")}
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={logout}>
                    <LogOut className="w-4 h-4 mr-2" />
                    {t("common.logout")}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl mb-2">{t("main.myLectures")}</h1>
            {lectureList.isSuccess && (
              <p className="text-muted-foreground">
                {t("main.lectureCount", { count: lectures.length })}
              </p>
            )}
          </div>
        </div>

        {lectureList.isPending ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : lectureList.isError ? (
          <div className="text-center py-20">
            <p className="text-muted-foreground mb-6">{t("lectures.loadFailed")}</p>
            <Button variant="outline" onClick={() => void lectureList.refetch()}>
              {t("lectures.retry")}
            </Button>
          </div>
        ) : lectures.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-xl mb-2">{t("main.noLecturesTitle")}</h3>
            <p className="text-muted-foreground mb-6">{t("main.noLecturesDesc")}</p>
            <Button onClick={openNewLecture} className="bg-[#3B72DD] hover:bg-[#4D82E0]">
              <Plus className="w-5 h-5 mr-2" />
              {t("main.startNewLecture")}
            </Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {lectures.map((lecture) => (
              <LectureCard
                key={lecture.id}
                lecture={lecture}
                onOpen={(lectureId) => navigate(`/lectures/${lectureId}`)}
                onDelete={setLectureToDelete}
              />
            ))}
          </div>
        )}
      </main>

      <NewLectureDialog open={newLectureOpen} onOpenChange={setNewLectureOpen} />
      <DeleteLectureDialog
        lecture={lectureToDelete}
        onCancel={() => setLectureToDelete(null)}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
