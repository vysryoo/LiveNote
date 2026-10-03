import { zodResolver } from "@hookform/resolvers/zod";
import type { ParseKeys } from "i18next";
import { ArrowLeft } from "lucide-react";
import { useForm } from "react-hook-form";
import { Trans, useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { z } from "zod";
import logoImage from "@/assets/logo.png";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { toAuthErrorKey } from "../api/errors";
import { useSignup } from "../hooks/useAuthMutations";
import { FieldError } from "./FieldError";

const signupSchema = z
  .object({
    loginId: z.string().min(1, "validation.required"),
    password: z.string().min(6, "validation.passwordMin"),
    passwordConfirm: z.string().min(1, "validation.required"),
    name: z.string().min(1, "validation.required"),
    email: z.email("validation.invalidEmail"),
  })
  .refine((values) => values.password === values.passwordConfirm, {
    path: ["passwordConfirm"],
    message: "validation.passwordMismatch",
  });

type SignupValues = z.infer<typeof signupSchema>;

const inputClassName =
  "h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20";
const linkClassName = "text-[rgb(59,114,221)] hover:underline";

export function SignupPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const signupMutation = useSignup();
  const form = useForm<SignupValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: { loginId: "", password: "", passwordConfirm: "", name: "", email: "" },
  });
  const { errors, isSubmitting } = form.formState;

  const onSubmit = form.handleSubmit(async ({ loginId, password, name, email }) => {
    let user;
    try {
      ({ user } = await signupMutation.mutateAsync({ loginId, password, name, email }));
    } catch (error) {
      form.setError("root", { message: toAuthErrorKey(error) });
      return;
    }
    navigate("/lectures");
    // 화면 언어는 사용자 정보 캐시 갱신 후 다음 렌더에서 바뀌므로 바뀔 언어를 직접 지정
    toast.success(t("auth.toast.signupSuccess", { lng: user.uiLanguage }));
  });

  const goToLanding = () => navigate("/");

  return (
    <div className="min-h-screen bg-[#F6F9FC] bg-wave-pattern-bottom flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <button
          type="button"
          onClick={goToLanding}
          className="flex items-center gap-2 text-[#525252] hover:text-[#2A2A2A] mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">{t("settings.back")}</span>
        </button>

        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-8">
          <div className="flex items-center mb-8 py-[0.4%]">
            <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
          </div>

          <div className="mb-8">
            <h1
              className="text-[2rem] leading-[1.3] mb-2 text-[#2A2A2A]"
              style={{ fontWeight: 600 }}
            >
              {t("signup.title")}
            </h1>
            <p className="text-[0.875rem] leading-[1.5] text-[#525252]">{t("signup.subtitle")}</p>
          </div>

          <form className="space-y-5" onSubmit={onSubmit} noValidate>
            <div className="space-y-2">
              <Label htmlFor="signup-username" className="text-sm text-[#2A2A2A]">
                {t("signup.username")}
              </Label>
              <Input
                id="signup-username"
                placeholder={t("signup.username")}
                className={inputClassName}
                {...form.register("loginId")}
              />
              <FieldError messageKey={errors.loginId?.message} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password" className="text-sm text-[#2A2A2A]">
                {t("signup.password")}
              </Label>
              <Input
                id="signup-password"
                type="password"
                placeholder={t("signup.password")}
                className={inputClassName}
                {...form.register("password")}
              />
              {errors.password ? (
                <FieldError messageKey={errors.password.message} />
              ) : (
                <p className="text-xs text-[#525252] mt-1">{t("signup.passwordHint")}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-confirm" className="text-sm text-[#2A2A2A]">
                {t("signup.passwordConfirm")}
              </Label>
              <Input
                id="signup-confirm"
                type="password"
                placeholder={t("signup.passwordConfirm")}
                className={inputClassName}
                {...form.register("passwordConfirm")}
              />
              <FieldError messageKey={errors.passwordConfirm?.message} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-name" className="text-sm text-[#2A2A2A]">
                {t("signup.name")}
              </Label>
              <Input
                id="signup-name"
                placeholder={t("signup.name")}
                className={inputClassName}
                {...form.register("name")}
              />
              <FieldError messageKey={errors.name?.message} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-email" className="text-sm text-[#2A2A2A]">
                {t("signup.email")}
              </Label>
              <Input
                id="signup-email"
                type="email"
                placeholder={t("signup.email")}
                className={inputClassName}
                {...form.register("email")}
              />
              <FieldError messageKey={errors.email?.message} />
            </div>

            {errors.root?.message && (
              <div className="bg-[#FF4D4D]/10 border border-[#FF4D4D]/20 text-[#FF4D4D] p-3 rounded-lg text-sm">
                {t(errors.root.message as ParseKeys)}
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#63A4FF] text-white rounded-lg h-11 mt-6 shadow-lg hover:shadow-xl transition-all"
              disabled={isSubmitting}
            >
              {isSubmitting ? `${t("signup.submit")}...` : t("signup.submit")}
            </Button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
            </div>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-[#525252]">
              {t("signup.haveAccount")}{" "}
              <button
                type="button"
                onClick={goToLanding}
                className={`${linkClassName} font-medium`}
              >
                {t("signup.loginLink")}
              </button>
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-xs text-[#525252]">
            <Trans
              i18nKey="signup.terms"
              components={{
                terms: <a href="#" className={linkClassName} />,
                privacy: <a href="#" className={linkClassName} />,
              }}
            />
          </p>
        </div>
      </div>
    </div>
  );
}
