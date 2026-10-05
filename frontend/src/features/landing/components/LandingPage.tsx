import { BookOpen, Check, Chrome, GraduationCap, Youtube } from "lucide-react";
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import ctaBackground from "@/assets/ctaBackground.png";
import logoImage from "@/assets/logo.png";
import { LoginDialog } from "@/features/auth/components/LoginDialog";
import { Button } from "@/shared/ui/button";
import { DemoVideoModal } from "./DemoVideoModal";
import GradientText from "./GradientText";

export function LandingPage() {
  // Trans에 t를 넘겨야 언어가 바뀔 때 다시 그려짐. 넘기지 않으면 React Compiler가 이전 언어의 Trans를 재사용함
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showDemoModal, setShowDemoModal] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const openLogin = () => setLoginOpen(true);
  const goToSignup = () => navigate("/signup");

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm shadow-lg">
        <div className="px-[3%] py-[0.4%]" style={{ fontSize: "clamp(14px, 1.2vw, 18px)" }}>
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <img src={logoImage} alt="LiveNote" style={{ height: "3em" }} />
            </div>

            <div className="flex" style={{ gap: "0.8em" }}>
              <Button
                variant="ghost"
                className="hover:bg-[#EEF2FF]"
                onClick={openLogin}
                style={{
                  background: "linear-gradient(135deg, #639BEE, #3B72DD)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                {t("login.login")}
              </Button>
              <Button
                className="bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#63A4FF] text-white rounded-lg px-6 shadow-md hover:shadow-lg transition-all"
                onClick={goToSignup}
              >
                {t("signup.title")}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section with Wave Background Container */}
      <section className="relative">
        {/* Hero Section Content */}
        <section className="pt-36 pb-26 px-8 relative z-10">
          <div className="max-w-[1400px] mx-auto relative z-10">
            <div className="text-center">
              <h1
                className="text-[5rem] leading-[1.1] mb-6 tracking-tight"
                style={{ fontWeight: 800 }}
              >
                <GradientText
                  colors={["#639BEE", "#3B72DD", "#4D82E0", "#83EAF1", "#639BEE"]}
                  animationSpeed={3}
                  showBorder={false}
                >
                  <Trans t={t} i18nKey="landing.hero.title" />
                </GradientText>
              </h1>
              <p className="text-[1.25rem] leading-[1.8] mb-10 text-[#4B5563] max-w-3xl mx-auto">
                <Trans t={t} i18nKey="landing.hero.desc" />
              </p>
              <div className="flex gap-4 justify-center">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#83EAF1] text-white rounded-lg w-[320px] h-[50px] text-lg shadow-lg hover:shadow-xl transition-all"
                  onClick={openLogin}
                >
                  {t("landing.startNow")}
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-0 hover:bg-[#EEF2FF] rounded-lg w-[320px] h-[50px] text-lg bg-white"
                  style={{
                    background: "linear-gradient(135deg, #639BEE, #3B72DD)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                  onClick={() => setShowDemoModal(true)}
                >
                  {t("landing.demoVideo")}
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Padding Area - 그라데이션 확장을 위한 공간 */}
        <div className="h-20 relative z-10" style={{ minHeight: "160px" }}></div>

        {/* Wave Background - 부모 컨테이너에 적용 (패딩 영역까지 포함) */}
        <div
          className="absolute inset-0 z-0"
          style={{
            backgroundImage: `
              radial-gradient(circle at center top, #639BEE 0%, #83EAF1 20%, #63A4FF 40%, transparent 70%)
            `,
            opacity: 0.55,
            mixBlendMode: "multiply",
          }}
        ></div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-8 bg-white">
        <div className="max-w-[1400px] mx-auto">
          {/* Feature 1: 실시간 음성 인식 및 전사 */}
          <div className="mb-32">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              {/* Left - Interface Preview */}
              <div className="relative">
                <div className="bg-[rgb(246,246,246)] rounded-2xl p-8 shadow-2xl">
                  <div className="flex items-center gap-2 mb-6">
                    <span className="ml-auto text-[#9CA3AF] text-sm">LiveNote Session</span>
                  </div>

                  <div className="space-y-6">
                    {/* 강의 기록 컴포넌트 */}
                    <div className="rounded-lg p-6 bg-white">
                      <h4 className="mb-4">{t("session.header.record")}</h4>
                      <p className="text-sm text-muted-foreground">
                        {t("landing.mock.transcript")}
                      </p>
                    </div>

                    {/* 실시간 요약 컴포넌트 */}
                    <div
                      className="rounded-lg p-6 bg-white hover:bg-muted cursor-pointer transition-all"
                      style={{
                        border: "2px solid transparent",
                        backgroundImage:
                          "linear-gradient(white, white), linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                        backgroundOrigin: "border-box",
                        backgroundClip: "padding-box, border-box",
                      }}
                    >
                      <h4 className="mb-4">{t("session.header.summary")}</h4>
                      <p className="text-sm text-muted-foreground">{t("landing.mock.summary")}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-3"></div>
                  </div>
                </div>
              </div>

              {/* Right - Description */}
              <div>
                <h3
                  className="text-[2.5rem] leading-[1.3] mb-6 text-[#1F2937]"
                  style={{ fontWeight: 700 }}
                >
                  {t("session.header.summary")}
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  {t("landing.summary.desc")}
                </p>

                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563] font-[Paperlogy]">
                      {t("landing.summary.point1")}
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      {t("landing.summary.point2")}
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      {t("landing.summary.point3")}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2: 원클릭 자료 탐색 */}
          <div className="mb-32">
            <div className="grid md:grid-cols-2 gap-16 items-stretch">
              {/* Left - Description */}
              <div>
                <h3
                  className="text-[2.5rem] leading-[1.3] mb-6 text-[#1F2937]"
                  style={{ fontWeight: 700 }}
                >
                  {t("landing.resources.title")}
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  <Trans t={t} i18nKey="landing.resources.desc" />
                </p>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div
                    className="rounded-xl p-5"
                    style={{
                      background:
                        "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                    }}
                  >
                    <div className="flex items-center mb-3">
                      <GraduationCap className="w-8 h-8 text-white" />
                    </div>
                    <div className="font-semibold text-white mb-1">
                      {t("session.resourceTypes.paper")}
                    </div>
                    <div className="text-sm text-white/90">{t("landing.resources.paperDesc")}</div>
                  </div>
                  <div
                    className="rounded-xl p-5"
                    style={{
                      background:
                        "linear-gradient(135deg, #63EE86, #5BA26D, #83F19E, #63FF8A, #3BDD64, #4DE072)",
                    }}
                  >
                    <div className="flex items-center mb-3">
                      <BookOpen className="w-8 h-8 text-white" />
                    </div>
                    <div className="font-semibold text-white mb-1">
                      {t("session.resourceTypes.wiki")}
                    </div>
                    <div className="text-sm text-white/90">{t("landing.resources.wikiDesc")}</div>
                  </div>
                  <div
                    className="rounded-xl p-5"
                    style={{
                      background:
                        "linear-gradient(135deg, #EE6363, #A25B5B, #F18383, #FF6363, #DD3B3B, #E04D4D)",
                    }}
                  >
                    <div className="flex items-center mb-3">
                      <Youtube className="w-8 h-8 text-white" />
                    </div>
                    <div className="font-semibold text-white mb-1">
                      {t("session.resourceTypes.video")}
                    </div>
                    <div className="text-sm text-white/90">{t("landing.resources.videoDesc")}</div>
                  </div>
                  <div
                    className="rounded-xl p-5"
                    style={{
                      background:
                        "linear-gradient(135deg, #A863EE, #7E5BA2, #BA83F1, #B163FF, #8C3BDD, #964DE0)",
                    }}
                  >
                    <div className="flex items-center mb-3">
                      <Chrome className="w-8 h-8 text-white" />
                    </div>
                    <div className="font-semibold text-white mb-1">
                      {t("session.resourceTypes.blog")}
                    </div>
                    <div className="text-sm text-white/90">{t("landing.resources.blogDesc")}</div>
                  </div>
                </div>
              </div>

              {/* Right - Resource Cards */}
              <div>
                <div className="bg-[rgb(246,246,246)] rounded-2xl p-8 shadow-2xl h-full">
                  <div className="flex items-center justify-between mb-4">
                    <span className="ml-auto text-[#9CA3AF] text-sm">LiveNote Session</span>
                  </div>

                  <div className="flex flex-col gap-3">
                    <div className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col">
                      <div className="flex items-start justify-between mb-3">
                        <span className="px-2 py-1 bg-[rgb(12,73,151)] text-xs text-[rgb(255,255,255)] rounded flex-shrink-0">
                          {t("session.resourceTypes.paper")}
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">Attention Is All You Need</p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          We present the Transformer, a model based entirely on self-attention
                          without recurrence or convolution...
                        </p>
                      </div>
                    </div>

                    <div
                      className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col"
                      style={{ animationDelay: "0.2s" }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="px-2 py-1 bg-[#960c0c] text-xs text-[rgb(255,255,255)] rounded flex-shrink-0">
                          {t("session.resourceTypes.video")}
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">
                          Transformers, the tech behind LLMs | Deep Learning Chapter 5
                        </p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          This video visually explains how Large Language Models (LLMs) work,
                          focusing on Transformers...
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 3: AI 질문 & 답변 성 */}
          <div className="mb-32">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              {/* Left - Question Cards */}
              <div className="space-y-4">
                {/* Question Card 1 */}
                <div className="bg-[rgb(246,246,246)] rounded-2xl p-8 shadow-2xl">
                  <div className="flex items-center justify-between mb-4">
                    <span className="ml-auto text-[#9CA3AF] text-sm">LiveNote Session</span>
                  </div>

                  <div className="flex flex-col gap-3">
                    <div className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col">
                      <div className="flex items-start justify-between mb-3">
                        <span className="px-2 py-1 bg-[#6b7280] text-xs text-[rgb(255,255,255)] rounded flex-shrink-0">
                          {t("session.qnaTypes.concept")}
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">{t("landing.qna.sampleQ1")}</p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {t("landing.qna.sampleA1")}
                        </p>
                      </div>
                    </div>

                    <div
                      className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col"
                      style={{ animationDelay: "0.1s" }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="px-2 py-1 bg-[#6b7280] text-xs text-[rgb(255,255,255)] rounded flex-shrink-0">
                          {t("session.qnaTypes.application")}
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">{t("landing.qna.sampleQ2")}</p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {t("landing.qna.sampleA2")}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right - Description */}
              <div>
                <h3
                  className="text-[2.5rem] leading-[1.3] mb-6 text-[#1F2937]"
                  style={{ fontWeight: 700 }}
                >
                  {t("landing.qna.title")}
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  <Trans t={t} i18nKey="landing.qna.desc" />
                </p>

                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      {t("landing.qna.point1")}
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      {t("landing.qna.point2")}
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      {t("landing.qna.point3")}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 4: 3단계로 간단하게 */}
          <div>
            <div className="text-center">
              <h3
                className="text-[3rem] leading-[1.2] mb-4 text-[#1F2937]"
                style={{ fontWeight: 700 }}
              >
                <Trans
                  t={t}
                  i18nKey="landing.steps.title"
                  components={{
                    highlight: (
                      <span
                        style={{
                          background:
                            "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                          WebkitBackgroundClip: "text",
                          WebkitTextFillColor: "transparent",
                          backgroundClip: "text",
                        }}
                      />
                    ),
                  }}
                />
              </h3>
              <p className="text-[1.125rem] text-[#6B7280] mb-16">{t("landing.steps.subtitle")}</p>

              {/* Steps */}
              <div className="grid md:grid-cols-3 gap-12 max-w-5xl mx-auto">
                {/* Step 1 */}
                <div className="relative">
                  <div className="flex flex-col items-center">
                    <div
                      className="w-24 h-24 rounded-full flex items-center justify-center mb-6 shadow-lg"
                      style={{
                        background:
                          "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                      }}
                    >
                      <span className="text-white text-4xl font-bold">1</span>
                    </div>
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">
                      {t("landing.steps.step1Title")}
                    </h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      <Trans t={t} i18nKey="landing.steps.step1Desc" />
                    </p>
                  </div>
                  {/* Connector Line */}
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#4D82E0] to-[#83EAF1]"></div>
                </div>

                {/* Step 2 */}
                <div className="relative">
                  <div className="flex flex-col items-center">
                    <div
                      className="w-24 h-24 rounded-full flex items-center justify-center mb-6 shadow-lg"
                      style={{
                        background:
                          "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                      }}
                    >
                      <span className="text-white text-4xl font-bold">2</span>
                    </div>
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">
                      {t("landing.steps.step2Title")}
                    </h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      <Trans t={t} i18nKey="landing.steps.step2Desc" />
                    </p>
                  </div>
                  {/* Connector Line */}
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#4D82E0] to-[#83EAF1]"></div>
                </div>

                {/* Step 3 */}
                <div>
                  <div className="flex flex-col items-center">
                    <div
                      className="w-24 h-24 rounded-full flex items-center justify-center mb-6 shadow-lg"
                      style={{
                        background:
                          "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                      }}
                    >
                      <span className="text-white text-4xl font-bold">3</span>
                    </div>
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">
                      {t("landing.steps.step3Title")}
                    </h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      <Trans t={t} i18nKey="landing.steps.step3Desc" />
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-8 relative overflow-hidden">
        {/* Background Image */}
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `url(${ctaBackground})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
        ></div>

        <div className="max-w-[1400px] mx-auto text-center relative z-10">
          <h2 className="text-[3rem] leading-[1.2] mb-6 text-white" style={{ fontWeight: 700 }}>
            {t("landing.cta.title")}
          </h2>
          <p className="text-[1.125rem] leading-[1.6] text-white/90 mb-8 max-w-2xl mx-auto">
            {t("landing.cta.desc")}
          </p>
          <Button
            size="lg"
            className="bg-white hover:bg-gray-50 rounded-lg px-8 py-6 h-auto shadow-lg hover:shadow-xl transition-all font-semibold"
            onClick={openLogin}
          >
            <span
              style={{
                background: "linear-gradient(135deg, #639BEE, #3B72DD, #4D82E0)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              {t("landing.startNow")}
            </span>
          </Button>

          {/* Copyright */}
          <div className="mt-16 pt-8 border-t border-white/20">
            <p className="text-sm text-white/60">© 2025 LiveNote. All rights reserved.</p>
          </div>
        </div>
      </section>

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* Demo Video Modal */}
      <DemoVideoModal isOpen={showDemoModal} onClose={() => setShowDemoModal(false)} />
      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} onSignupClick={goToSignup} />
    </div>
  );
}
