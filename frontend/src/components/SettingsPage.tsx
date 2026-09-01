import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { ArrowLeft } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useI18n, codeToLanguage, languageToCode, type SupportedLanguage } from "../i18n/I18nContext";

interface SettingsPageProps {
  onBack: () => void;
  onSave: (data: { language: string; currentPassword?: string; newPassword?: string }) => Promise<void> | void;
  currentLanguage: string;
}

export function SettingsPage({ onBack, onSave, currentLanguage }: SettingsPageProps) {
  const { t } = useI18n();
  const [language, setLanguage] = useState<SupportedLanguage>(() => codeToLanguage(currentLanguage));
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Prop 변경 시 셀렉트 기본값 동기화 (user.uiLanguage 반영)
  // DB에서 읽은 코드를 표시명으로 변환
  useEffect(() => {
    const displayLang = codeToLanguage(currentLanguage);
    setLanguage(displayLang);
  }, [currentLanguage]);

  const handleSave = async () => {
    setError("");

    if (newPassword && newPassword !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다");
      return;
    }

    if (newPassword && newPassword.length < 6) {
      setError("비밀번호는 최소 6자 이상이어야 합니다");
      return;
    }
    if (newPassword && !currentPassword) {
      setError("현재 비밀번호를 입력해주세요");
      return;
    }
    if (submitting) return;

    setSubmitting(true);
    try {
      // 언어 표시명을 DB 코드로 변환하여 저장
      const languageCode = languageToCode(language);
      await onSave({ 
        language: languageCode,
        ...(currentPassword ? { currentPassword } : {}),
        ...(newPassword ? { newPassword } : {}),
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "설정을 저장하지 못했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background bg-wave-pattern-bottom">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: 'clamp(14px, 1.2vw, 18px)' }}>
          <button 
            onClick={onBack}
            className="flex items-center text-muted-foreground hover:text-foreground"
            style={{ gap: '0.5em' }}
          >
            <ArrowLeft style={{ width: '1.2em', height: '1.2em' }} />
            {t("settings.back")}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl mb-8">{t("settings.title")}</h1>

          <div className="bg-white rounded-lg border p-8 space-y-6">
            <div className="space-y-2">
              <Label>{t("common.language")}</Label>
              <Select value={language} onValueChange={(value) => setLanguage(value as SupportedLanguage)}>
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

            <div className="border-t pt-6">
              <h3 className="text-lg mb-4">{t("settings.changePassword")}</h3>
              
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">{t("settings.currentPassword")}</Label>
                  <Input 
                    id="current-password"
                    type="password"
                    placeholder={t("settings.currentPasswordPH")}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password">{t("settings.newPassword")}</Label>
                  <Input 
                    id="new-password"
                    type="password"
                    placeholder={t("settings.newPasswordPH")}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">{t("settings.confirmPassword")}</Label>
                  <Input 
                    id="confirm-password"
                    type="password"
                    placeholder={t("settings.confirmPasswordPH")}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>

                {error && (
                  <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                    {error}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4">
              <Button 
                className="w-full bg-[#3B72DD] hover:bg-[#4D82E0]"
                onClick={handleSave}
                disabled={submitting}
              >
                {submitting ? `${t("settings.save")}...` : t("settings.save")}
              </Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}