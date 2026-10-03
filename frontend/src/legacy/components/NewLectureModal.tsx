import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Button } from "@/shared/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { X, Upload, FileText } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useI18n, languageToCode, type SupportedLanguage } from "../i18n/I18nContext";

interface NewLectureModalProps {
  open: boolean;
  onClose: () => void;
  onStart: (data: {
    language: string;
    category: string;
    subject: string;
    files: File[];
  }) => Promise<void> | void;
}

export function NewLectureModal({ open, onClose, onStart }: NewLectureModalProps) {
  const { t, language: uiLanguage } = useI18n();
  const [language, setLanguage] = useState(uiLanguage);
  const [category, setCategory] = useState("");
  const [subject, setSubject] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles([...files, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleStart = async () => {
    if (!category || !subject || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      // 언어 표시명을 DB 코드로 변환하여 저장
      const languageCode = languageToCode(language);
      await onStart({ language: languageCode, category, subject, files });
      setLanguage("한국어");
      setCategory("");
      setSubject("");
      setFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "강의를 시작하지 못했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  // 모달이 열리거나 uiLanguage가 바뀔 때 드롭다운 기본값을 동기화
  // (사용자가 수동으로 바꾼 경우 모달 닫혔다 열릴 때만 초기화되도록 open 조건 포함)
  useEffect(() => {
    if (open) {
      setLanguage(uiLanguage);
    }
  }, [uiLanguage, open]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
        <DialogHeader>
          <DialogTitle>{t("newLecture.title")}</DialogTitle>
          <DialogDescription>{t("newLecture.desc")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label>{t("common.language")}</Label>
            <Select
              value={language}
              onValueChange={(value) => setLanguage(value as SupportedLanguage)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="한국어">한국어</SelectItem>
                <SelectItem value="English">English</SelectItem>
                <SelectItem value="日本語">日本語</SelectItem>
                <SelectItem value="汉语">汉语</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>{t("newLecture.category")}</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger>
                <SelectValue placeholder={t("newLecture.categoryPH")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Computer Science">Computer Science</SelectItem>
                <SelectItem value="Mathematics">Mathematics</SelectItem>
                <SelectItem value="Physics">Physics</SelectItem>
                <SelectItem value="Chemistry">Chemistry</SelectItem>
                <SelectItem value="Biology">Biology</SelectItem>
                <SelectItem value="Econimics">Economics</SelectItem>
                <SelectItem value="Others">Others</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="subject">{t("newLecture.subject")}</Label>
            <Input
              id="subject"
              placeholder={t("newLecture.subjectPH")}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>{t("newLecture.filesOptional")}</Label>
            <div className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-[#639BEE] transition-colors">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                multiple
                onChange={handleFileSelect}
                accept=".pdf,.doc,.docx,.txt,.ppt,.pptx"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">{t("newLecture.clickToAddFiles")}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {t("newLecture.supportedTypes")}
                </p>
              </label>
            </div>
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <Label>{t("newLecture.addedFiles")}</Label>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-muted p-3 rounded-lg"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm">{file.name}</span>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
              {error}
            </div>
          )}
          <Button
            className="w-full bg-[#3B72DD] hover:bg-[#4D82E0]"
            onClick={handleStart}
            disabled={!category || !subject || submitting}
          >
            {submitting ? `${t("main.startNewLecture")}...` : t("main.startNewLecture")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
