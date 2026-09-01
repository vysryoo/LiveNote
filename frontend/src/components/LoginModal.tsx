import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { X } from "lucide-react";
import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";

interface LoginModalProps {
  open: boolean;
  onClose: () => void;
  onLogin: (loginId: string, password: string) => Promise<void> | void;
  onSignupClick: () => void;
}

export function LoginModal({ open, onClose, onLogin, onSignupClick }: LoginModalProps) {
  const { t } = useI18n();
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    if (!loginId || !password || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await onLogin(loginId, password);
      setLoginId("");
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
        >
          <X className="h-4 w-4" />
        </button>
        <DialogHeader>
          <DialogTitle>{t("login.title")}</DialogTitle>
          <DialogDescription>{t("login.desc")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="username">{t("login.username")}</Label>
            <Input
              id="username"
              placeholder={t("login.username")}
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">{t("login.password")}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t("login.password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            />
          </div>
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
              {error}
            </div>
          )}
          <Button
            className="w-full bg-[rgb(59,114,221)] hover:bg-[#4D82E0] text-[rgb(255,255,255)]"
            onClick={handleLogin}
            disabled={submitting || !loginId || !password}
          >
            {submitting ? `${t("login.login")}...` : t("login.login")}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            {/* keep sentence minimal; only link translated */}
            <button
              onClick={() => {
                onClose();
                onSignupClick();
              }}
              className="text-[#3B72DD] hover:underline"
            >
              {t("login.signupLink")}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
