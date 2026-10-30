import { Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { useLogout } from "@/features/auth/hooks/useLogout";
import { AppHeader, AppLogo } from "@/shared/components/AppHeader";
import { UserMenu } from "@/shared/components/UserMenu";
import { Button } from "@/shared/ui/button";
import type { Lecture } from "../api/schemas";
import { useLectureList } from "../hooks/useLectureList";
import { useDeleteLecture } from "../hooks/useLectureMutations";
import { mergeLecturePages } from "../lib/lectureDisplay";
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

  const lectures = mergeLecturePages(lectureList.data?.pages ?? []);
  // 전체 강의 수는 가장 최근에 받은 페이지 기준
  const totalCount = lectureList.data?.pages.at(-1)?.total ?? lectures.length;
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
    <div className="min-h-screen bg-background">
      <AppHeader>
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <AppLogo />
          </div>

          <div className="flex items-center" style={{ gap: "1.2em" }}>
            <Button variant="brand" onClick={openNewLecture}>
              <Plus style={{ width: "1.4em", height: "1.4em", marginRight: "0.5em" }} />
              {t("main.startNewLecture")}
            </Button>
            <UserMenu onSettingsClick={() => navigate("/settings")} onLogoutClick={logout} />
          </div>
        </div>
      </AppHeader>

      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl mb-2">{t("main.myLectures")}</h1>
            {lectureList.isSuccess && (
              <p className="text-muted-foreground">
                {t("main.lectureCount", { count: totalCount })}
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
            <Button variant="brand" onClick={openNewLecture}>
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
        {lectureList.hasNextPage && (
          <div className="flex justify-center mt-8">
            <Button
              variant="outline"
              disabled={lectureList.isFetchingNextPage}
              onClick={() => void lectureList.fetchNextPage()}
            >
              {lectureList.isFetchingNextPage && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {t("lectures.loadMore")}
            </Button>
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
