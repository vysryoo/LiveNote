import { zodResolver } from "@hookform/resolvers/zod";
import type { ParseKeys } from "i18next";
import { FileText, Upload, X } from "lucide-react";
import { Controller, useForm, useWatch } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";
import { FieldError } from "@/shared/components/FieldError";
import { isLanguageCode, LANGUAGE_CODES, LANGUAGE_LABELS } from "@/shared/i18n";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useCreateLecture } from "../hooks/useLectureMutations";
import { LECTURE_CATEGORIES } from "../lectureDisplay";

const newLectureSchema = z.object({
  sttLanguage: z.enum(LANGUAGE_CODES),
  subject: z.string().min(1, "validation.required"),
  title: z.string().trim().min(1, "validation.required"),
  // 백엔드가 PDF 한 개만 받아 RAG에 업서트함
  file: z
    .instanceof(File)
    .refine((file) => file.type === "application/pdf", "newLecture.pdfOnly")
    .optional(),
});

type NewLectureValues = z.infer<typeof newLectureSchema>;

type NewLectureDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function NewLectureDialog({ open, onOpenChange }: NewLectureDialogProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const createMutation = useCreateLecture();
  const form = useForm<NewLectureValues>({
    resolver: zodResolver(newLectureSchema),
    defaultValues: {
      // 강의 음성 언어는 화면 언어와 같은 경우가 많아 기본값으로 사용
      sttLanguage: isLanguageCode(i18n.language) ? i18n.language : "ko",
      subject: "",
      title: "",
      file: undefined,
    },
  });
  const { errors, isSubmitting } = form.formState;
  const file = useWatch({ control: form.control, name: "file" });

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) form.reset();
    onOpenChange(nextOpen);
  };

  const onSubmit = form.handleSubmit(async (values) => {
    let lectureId;
    try {
      ({ id: lectureId } = await createMutation.mutateAsync(values));
    } catch {
      form.setError("root", { message: "newLecture.createFailed" });
      return;
    }
    handleOpenChange(false);
    navigate(`/lectures/${lectureId}`);
    toast.success(t("lectures.toast.created"));
  });

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("newLecture.title")}</DialogTitle>
          <DialogDescription>{t("newLecture.desc")}</DialogDescription>
        </DialogHeader>
        <form className="space-y-4 pt-4" onSubmit={onSubmit} noValidate>
          <div className="space-y-2">
            <Label>{t("common.language")}</Label>
            <Controller
              control={form.control}
              name="sttLanguage"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGE_CODES.map((code) => (
                      <SelectItem key={code} value={code}>
                        {LANGUAGE_LABELS[code]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("newLecture.category")}</Label>
            <Controller
              control={form.control}
              name="subject"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("newLecture.categoryPH")} />
                  </SelectTrigger>
                  <SelectContent>
                    {LECTURE_CATEGORIES.map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            <FieldError messageKey={errors.subject?.message} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">{t("newLecture.subject")}</Label>
            <Input
              id="subject"
              placeholder={t("newLecture.subjectPH")}
              {...form.register("title")}
            />
            <FieldError messageKey={errors.title?.message} />
          </div>

          <div className="space-y-2">
            <Label>{t("newLecture.filesOptional")}</Label>
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-[#639BEE] transition-colors">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                accept=".pdf,application/pdf"
                onChange={(e) => {
                  const selected = e.target.files?.[0];
                  if (selected) form.setValue("file", selected, { shouldValidate: true });
                  // 같은 파일을 지웠다가 다시 고를 때도 change 이벤트가 발생하도록 초기화
                  e.target.value = "";
                }}
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">{t("newLecture.clickToAddFiles")}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {t("newLecture.supportedTypes")}
                </p>
              </label>
            </div>
            <FieldError messageKey={errors.file?.message} />
          </div>

          {file && (
            <div className="space-y-2">
              <Label>{t("newLecture.addedFiles")}</Label>
              <div className="flex items-center justify-between bg-muted p-3 rounded-lg">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{file.name}</span>
                </div>
                <button
                  type="button"
                  onClick={() => form.setValue("file", undefined, { shouldValidate: true })}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {errors.root?.message && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
              {t(errors.root.message as ParseKeys)}
            </div>
          )}
          <Button
            type="submit"
            className="w-full bg-[#3B72DD] hover:bg-[#4D82E0]"
            disabled={isSubmitting}
          >
            {isSubmitting ? `${t("main.startNewLecture")}...` : t("main.startNewLecture")}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
