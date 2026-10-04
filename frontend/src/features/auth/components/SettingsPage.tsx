import { zodResolver } from "@hookform/resolvers/zod";
import type { ParseKeys } from "i18next";
import { ArrowLeft } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";
import { LANGUAGE_CODES, LANGUAGE_LABELS } from "@/shared/i18n";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { toAuthErrorKey } from "../api/errors";
import type { User } from "../api/schemas";
import { useUpdateSettings } from "../hooks/useAuthMutations";
import { useMe } from "../hooks/useMe";
import { FieldError } from "@/shared/components/FieldError";

const settingsSchema = z
  .object({
    language: z.enum(LANGUAGE_CODES),
    currentPassword: z.string(),
    newPassword: z.string(),
    confirmPassword: z.string(),
  })
  .superRefine((values, ctx) => {
    // 비밀번호 칸을 비워 두면 언어만 저장
    if (!values.newPassword) return;
    if (values.newPassword.length < 6) {
      ctx.addIssue({ code: "custom", path: ["newPassword"], message: "validation.passwordMin" });
    }
    if (values.newPassword !== values.confirmPassword) {
      ctx.addIssue({
        code: "custom",
        path: ["confirmPassword"],
        message: "validation.passwordMismatch",
      });
    }
    if (!values.currentPassword) {
      ctx.addIssue({
        code: "custom",
        path: ["currentPassword"],
        message: "validation.currentPasswordRequired",
      });
    }
  });

type SettingsValues = z.infer<typeof settingsSchema>;

export function SettingsPage() {
  const { data: user } = useMe();
  // RequireAuth를 통과한 뒤에만 렌더되므로 user는 항상 존재
  if (!user) return null;
  return <SettingsForm user={user} />;
}

function SettingsForm({ user }: { user: User }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const settingsMutation = useUpdateSettings();
  const form = useForm<SettingsValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      language: user.uiLanguage,
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
    },
  });
  const { errors, isSubmitting } = form.formState;

  const goToLectures = () => navigate("/lectures");

  const onSubmit = form.handleSubmit(async ({ language, currentPassword, newPassword }) => {
    const password = newPassword ? { currentPassword, newPassword } : undefined;
    let user;
    try {
      user = await settingsMutation.mutateAsync({ language, password });
    } catch (error) {
      form.setError("root", { message: toAuthErrorKey(error) });
      return;
    }
    // 화면 언어는 사용자 정보 캐시 갱신 후 다음 렌더에서 바뀌므로 바뀔 언어를 직접 지정
    const lng = user.uiLanguage;
    if (password) toast.success(t("auth.toast.passwordChanged", { lng }));
    toast.success(t("auth.toast.settingsSaved", { lng }));
    goToLectures();
  });

  return (
    <div className="min-h-screen bg-background bg-wave-pattern-bottom">
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
          <button
            type="button"
            onClick={goToLectures}
            className="flex items-center text-muted-foreground hover:text-foreground"
            style={{ gap: "0.5em" }}
          >
            <ArrowLeft style={{ width: "1.2em", height: "1.2em" }} />
            {t("settings.back")}
          </button>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-12">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl mb-8">{t("settings.title")}</h1>

          <form className="bg-white rounded-lg border p-8 space-y-6" onSubmit={onSubmit} noValidate>
            <div className="space-y-2">
              <Label>{t("common.language")}</Label>
              <Controller
                control={form.control}
                name="language"
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

            <div className="border-t pt-6">
              <h3 className="text-lg mb-4">{t("settings.changePassword")}</h3>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">{t("settings.currentPassword")}</Label>
                  <Input
                    id="current-password"
                    type="password"
                    placeholder={t("settings.currentPasswordPH")}
                    {...form.register("currentPassword")}
                  />
                  <FieldError messageKey={errors.currentPassword?.message} />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="new-password">{t("settings.newPassword")}</Label>
                  <Input
                    id="new-password"
                    type="password"
                    placeholder={t("settings.newPasswordPH")}
                    {...form.register("newPassword")}
                  />
                  <FieldError messageKey={errors.newPassword?.message} />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirm-password">{t("settings.confirmPassword")}</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder={t("settings.confirmPasswordPH")}
                    {...form.register("confirmPassword")}
                  />
                  <FieldError messageKey={errors.confirmPassword?.message} />
                </div>

                {errors.root?.message && (
                  <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                    {t(errors.root.message as ParseKeys)}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4">
              <Button
                type="submit"
                className="w-full bg-[#3B72DD] hover:bg-[#4D82E0]"
                disabled={isSubmitting}
              >
                {isSubmitting ? `${t("settings.save")}...` : t("settings.save")}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}
