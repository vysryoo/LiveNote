import { zodResolver } from "@hookform/resolvers/zod";
import type { ParseKeys } from "i18next";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";
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
import { toAuthErrorKey } from "../api/errors";
import { useLogin } from "../hooks/useAuthMutations";
import { FieldError } from "./FieldError";

const loginSchema = z.object({
  loginId: z.string().min(1, "validation.required"),
  password: z.string().min(1, "validation.required"),
});

type LoginValues = z.infer<typeof loginSchema>;

type LoginDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSignupClick: () => void;
};

export function LoginDialog({ open, onOpenChange, onSignupClick }: LoginDialogProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const loginMutation = useLogin();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { loginId: "", password: "" },
  });
  const { errors, isSubmitting } = form.formState;

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) form.reset();
    onOpenChange(nextOpen);
  };

  const onSubmit = form.handleSubmit(async (values) => {
    let user;
    try {
      ({ user } = await loginMutation.mutateAsync(values));
    } catch (error) {
      form.setError("root", { message: toAuthErrorKey(error) });
      return;
    }
    handleOpenChange(false);
    navigate("/lectures");
    // 화면 언어는 사용자 정보 캐시 갱신 후 다음 렌더에서 바뀌므로 바뀔 언어를 직접 지정
    toast.success(t("auth.toast.loginSuccess", { lng: user.uiLanguage }));
  });

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("login.title")}</DialogTitle>
          <DialogDescription>{t("login.desc")}</DialogDescription>
        </DialogHeader>
        <form className="space-y-4 pt-4" onSubmit={onSubmit} noValidate>
          <div className="space-y-2">
            <Label htmlFor="username">{t("login.username")}</Label>
            <Input id="username" placeholder={t("login.username")} {...form.register("loginId")} />
            <FieldError messageKey={errors.loginId?.message} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">{t("login.password")}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t("login.password")}
              {...form.register("password")}
            />
            <FieldError messageKey={errors.password?.message} />
          </div>
          {errors.root?.message && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-md p-2">
              {t(errors.root.message as ParseKeys)}
            </div>
          )}
          <Button
            type="submit"
            className="w-full bg-[rgb(59,114,221)] hover:bg-[#4D82E0] text-[rgb(255,255,255)]"
            disabled={isSubmitting}
          >
            {isSubmitting ? `${t("login.login")}...` : t("login.login")}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            <button
              type="button"
              onClick={() => {
                handleOpenChange(false);
                onSignupClick();
              }}
              className="text-[#3B72DD] hover:underline"
            >
              {t("login.signupLink")}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
