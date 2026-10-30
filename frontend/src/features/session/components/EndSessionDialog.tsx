import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import { FieldError } from "@/shared/components/FieldError";
import { FormError } from "@/shared/components/FormError";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";

const endSessionSchema = z.object({
  title: z.string().trim().min(1, "validation.required"),
});

type EndSessionValues = z.infer<typeof endSessionSchema>;

type EndSessionDialogProps = {
  open: boolean;
  defaultTitle: string;
  onCancel: () => void;
  onSaveAndEnd: (title: string) => Promise<void>;
};

/**
 * 강의 이름을 받아 저장하고 종료하는 대화창을 표시한다.
 *
 * @param props.onSaveAndEnd 저장 처리. 실패하면 예외를 던져야 대화창 안에 오류가 표시됨
 */
export function EndSessionDialog({
  open,
  defaultTitle,
  onCancel,
  onSaveAndEnd,
}: EndSessionDialogProps) {
  const { t } = useTranslation();
  const form = useForm<EndSessionValues>({
    resolver: zodResolver(endSessionSchema),
    values: { title: defaultTitle },
  });
  const { errors, isSubmitting } = form.formState;

  const onSubmit = form.handleSubmit(async ({ title }) => {
    try {
      await onSaveAndEnd(title);
    } catch {
      form.setError("root", { message: "lectures.endFailed" });
    }
  });

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onCancel()}>
      <DialogContent className="sm:max-w-md z-[100]">
        <DialogHeader>
          <DialogTitle>{t("endSession.title")}</DialogTitle>
          <DialogDescription>{t("endSession.desc")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} noValidate>
          <div className="space-y-4 pt-4">
            <div className="space-y-2">
              <Label htmlFor="session-name">{t("endSession.inputLabel")}</Label>
              <Input
                id="session-name"
                placeholder={t("endSession.inputPlaceholder")}
                {...form.register("title")}
              />
              <FieldError messageKey={errors.title?.message} />
            </div>
            <FormError messageKey={errors.root?.message} />
          </div>
          <DialogFooter className="gap-2 sm:gap-0 pt-4">
            <Button type="button" variant="outline" onClick={onCancel}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" variant="brand" disabled={isSubmitting}>
              {isSubmitting ? `${t("common.save")}...` : t("common.saveAndEnd")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
