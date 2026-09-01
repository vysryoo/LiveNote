import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useI18n } from "../i18n/I18nContext";

interface EndSessionModalProps {
  open: boolean;
  onClose: () => void;
  onSaveAndEnd: (sessionName: string) => void;
  defaultName?: string;
}

export function EndSessionModal({
  open,
  onClose,
  onSaveAndEnd,
  defaultName = "",
}: EndSessionModalProps) {
  const { t } = useI18n();
  const [sessionName, setSessionName] = useState(defaultName);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSessionName(defaultName);
      setError(null);
      setSubmitting(false);
    }
  }, [defaultName, open]);

  const handleSave = async () => {
    const trimmed = sessionName.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSaveAndEnd(trimmed);
      setSessionName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "강의를 종료하지 못했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md z-[100]">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
        <DialogHeader>
          <DialogTitle>{t("endSession.title")}</DialogTitle>
          <DialogDescription>{t("endSession.desc")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="session-name">{t("endSession.inputLabel")}</Label>
            <Input
              id="session-name"
              placeholder="강의 이름을 입력하세요"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
            />
          </div>
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
              {error}
            </div>
          )}
        </div>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            className="bg-[#3B72DD] hover:bg-[#4D82E0]"
            onClick={handleSave}
            disabled={!sessionName.trim() || submitting}
          >
            {submitting ? `${t("common.save")}...` : t("common.saveAndEnd")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
