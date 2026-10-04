import { useTranslation } from "react-i18next";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import type { Lecture } from "../api/schemas";

type DeleteLectureDialogProps = {
  lecture: Lecture | null;
  onCancel: () => void;
  onConfirm: () => void;
};

/**
 * 강의 삭제 확인창을 표시한다.
 *
 * @param props.lecture 삭제할 강의. `null`이면 확인창을 닫음
 */
export function DeleteLectureDialog({ lecture, onCancel, onConfirm }: DeleteLectureDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={lecture !== null} onOpenChange={(open) => !open && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("lectures.delete.title")}</AlertDialogTitle>
          <AlertDialogDescription>
            {t("lectures.delete.desc", { title: lecture?.title || t("lectures.untitled") })}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {t("common.delete")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
