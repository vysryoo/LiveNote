import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import React, { useState } from "react";
import { ArrowLeft } from "lucide-react";
import logoImage from "@/assets/logo.png";
import { useI18n } from "../i18n/I18nContext";

interface SignupPageProps {
  onSignup: (data: {
    loginId: string;
    email: string;
    password: string;
    name: string;
  }) => Promise<void> | void;
  onBack: () => void;
}

export function SignupPage({ onSignup, onBack }: SignupPageProps) {
  const { t } = useI18n();
  const [loginId, setLoginId] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setError("");

    if (!loginId || !email || !password || !confirmPassword || !name) {
      setError("모든 필드를 입력해주세요");
      return;
    }

    if (password !== confirmPassword) {
      setError("비밀번호가 일치하지 않습니다");
      return;
    }

    if (password.length < 6) {
      setError("비밀번호는 최소 6자 이상이어야 합니다");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("유효한 이메일 주소를 입력해주세요");
      return;
    }
    if (submitting) return;
    setSubmitting(true);
    try {
      await onSignup({ loginId, email, password, name });
    } catch (err) {
      setError(err instanceof Error ? err.message : "회원가입에 실패했습니다");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F9FC] bg-wave-pattern-bottom flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Back Button */}
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-[#525252] hover:text-[#2A2A2A] mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">{t("settings.back")}</span>
        </button>

        {/* Signup Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-8">
          {/* Logo */}
          <div className="flex items-center mb-8 py-[0.4%]">
            <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
          </div>

          {/* Header */}
          <div className="mb-8">
            <h1
              className="text-[2rem] leading-[1.3] mb-2 text-[#2A2A2A]"
              style={{ fontWeight: 600 }}
            >
              {t("signup.title")}
            </h1>
            <p className="text-[0.875rem] leading-[1.5] text-[#525252]">
              LiveNote와 함께 강력한 AI 기능을 경험하세요
            </p>
          </div>

          {/* Form */}
          <div className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="signup-username" className="text-sm text-[#2A2A2A]">
                {t("signup.username")}
              </Label>
              <Input
                id="signup-username"
                placeholder={t("signup.username")}
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                className="h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-password" className="text-sm text-[#2A2A2A]">
                {t("signup.password")}
              </Label>
              <Input
                id="signup-password"
                type="password"
                placeholder={t("signup.password")}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20"
              />
              <p className="text-xs text-[#525252] mt-1">최소 6자 이상 입력해주세요</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-confirm" className="text-sm text-[#2A2A2A]">
                {t("signup.passwordConfirm")}
              </Label>
              <Input
                id="signup-confirm"
                type="password"
                placeholder={t("signup.passwordConfirm")}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-name" className="text-sm text-[#2A2A2A]">
                {t("signup.name")}
              </Label>
              <Input
                id="signup-name"
                placeholder={t("signup.name")}
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="signup-email" className="text-sm text-[#2A2A2A]">
                {t("signup.email")}
              </Label>
              <Input
                id="signup-email"
                type="email"
                placeholder={t("signup.email")}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 rounded-lg border-gray-200 focus:border-[#635BFF] focus:ring-[#635BFF]/20"
              />
            </div>

            {error && (
              <div className="bg-[#FF4D4D]/10 border border-[#FF4D4D]/20 text-[#FF4D4D] p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <Button
              className="w-full bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#63A4FF] text-white rounded-lg h-11 mt-6 shadow-lg hover:shadow-xl transition-all"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? `${t("signup.submit")}...` : t("signup.submit")}
            </Button>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
            </div>

            {/* Social Login (Optional) */}
            <div className="space-y-3"></div>
          </div>

          {/* Login Link */}
          <div className="mt-8 text-center">
            <p className="text-sm text-[#525252]">
              이미 계정이 있으신가요?{" "}
              <button
                onClick={onBack}
                className="text-[rgb(59,114,221)] hover:underline font-medium"
              >
                로그인
              </button>
            </p>
          </div>
        </div>

        {/* Terms */}
        <div className="mt-6 text-center">
          <p className="text-xs text-[#525252]">
            회원가입을 진행하면{" "}
            <a href="#" className="text-[rgb(59,114,221)] hover:underline">
              이용약관
            </a>{" "}
            및{" "}
            <a href="#" className="text-[rgb(59,114,221)] hover:underline">
              개인정보처리방침
            </a>
            에 동의하는 것으로 간주됩니다.
          </p>
        </div>
      </div>
    </div>
  );
}
