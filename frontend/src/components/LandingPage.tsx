import { Button } from "./ui/button";
import { Check, Chrome, BookOpen, Youtube, GraduationCap } from "lucide-react";
import ctaBackground from "figma:asset/ctaBackground.png";
import logoImage from "figma:asset/logo.png";
import GradientText from "./GradientText";
import { DemoVideoModal } from "./DemoVideoModal";
import { useState } from "react";

interface LandingPageProps {
  onLoginClick: () => void;
  onSignupClick: () => void;
}

export function LandingPage({ onLoginClick, onSignupClick }: LandingPageProps) {
  const [showDemoModal, setShowDemoModal] = useState(false);

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
                onClick={onLoginClick}
                style={{
                  background: "linear-gradient(135deg, #639BEE, #3B72DD)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                로그인
              </Button>
              <Button
                className="bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#63A4FF] text-white rounded-lg px-6 shadow-md hover:shadow-lg transition-all"
                onClick={onSignupClick}
              >
                회원가입
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
                  클릭 한 번으로
                  <br />
                  학습 흐름을 유지하세요
                </GradientText>
              </h1>
              <p className="text-[1.25rem] leading-[1.8] mb-10 text-[#4B5563] max-w-3xl mx-auto">
                실시간 텍스트 변환 및 요약으로 집중력을 높이고
                <br />
                원클릭 자료탐색과 AI 질문답변으로 학습 효율을 극대화하세요
              </p>
              <div className="flex gap-4 justify-center">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-[#639BEE] via-[#3B72DD] to-[#4D82E0] hover:from-[#5B60A2] hover:to-[#83EAF1] text-white rounded-lg w-[320px] h-[50px] text-lg shadow-lg hover:shadow-xl transition-all"
                  onClick={onLoginClick}
                >
                  지금 시작하기 →
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
                  데모 비디오
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
                      <h4 className="mb-4">강의 기록</h4>
                      <p className="text-sm text-muted-foreground">
                        오늘은 인공지능의 언어 이해를 혁신적으로 바꾼 Transformer 모델을
                        다뤄보겠습니다. 이전의 RNN이나 CNN 기반 모델들은 순차적 연산으로 병렬화가
                        어려웠죠. 하지만 Transformer는 이를 Self-Attention 메커니즘으로 완전히
                        대체하여, 문장 내 단어 간 관계를 한 번에 파악하고 훨씬 빠르고 효율적인
                        학습을 가능하게...
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
                      <h4 className="mb-4">실시간 요약</h4>
                      <p className="text-sm text-muted-foreground">
                        Transformer는 RNN·CNN을 대체한 Self-Attention 기반 구조로, 병렬 연산과 문맥
                        이해를 동시에 개선해 현대 언어모델의 핵심이 됨.
                      </p>
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
                  실시간 요약
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  강의 흐름을 그대로 따라갑니다. 실시간 요약으로 놓침 없이 이해하세요.
                </p>

                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563] font-[Paperlogy]">
                      정확한 음성 인식
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      핵심 정보의 실시간 요약 제공
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      음성 인식 기반 정리된 학습 히스토리 제공
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
                  원클릭 자료 탐색
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  검색어 입력도, 수많은 결과 속 선별도 이제 필요 없습니다.<br></br>
                  AI가 가장 적절한 자료를 한 번에 연결해드립니다
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
                    <div className="font-semibold text-white mb-1">학술자료</div>
                    <div className="text-sm text-white/90">논문, 연구 자료</div>
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
                    <div className="font-semibold text-white mb-1">위키백과</div>
                    <div className="text-sm text-white/90">기본 개념 설명</div>
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
                    <div className="font-semibold text-white mb-1">유튜브</div>
                    <div className="text-sm text-white/90">시각적 학습 자료</div>
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
                    <div className="font-semibold text-white mb-1">웹/블로그</div>
                    <div className="text-sm text-white/90">실무 예제, 튜토리얼</div>
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
                          학술자료
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
                          유튜브
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
                          개념확인
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">
                          Transformer는 왜 RNN보다 빠르다고 하나요?
                        </p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          Transformer는 순차적으로 단어를 처리하지 않고, 모든 단어 간 관계를 병렬로
                          계산합니다...
                        </p>
                      </div>
                    </div>

                    <div
                      className="border rounded-lg p-6 bg-white flex-1 opacity-0 animate-[fadeInUp_0.4s_ease_forwards] flex flex-col"
                      style={{ animationDelay: "0.1s" }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="px-2 py-1 bg-[#6b7280] text-xs text-[rgb(255,255,255)] rounded flex-shrink-0">
                          응용확장
                        </span>
                      </div>
                      <div className="mb-3">
                        <p className="font-medium text-[#1F2937]">
                          Positional Encoding은 왜 꼭 필요한가요?
                        </p>
                      </div>
                      <div className="flex-1 overflow-hidden">
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          Transformer는 순서를 따라가며 처리하지 않기 때문에, 위치 정보를 따로
                          제공해야 합니다...
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
                  AI 질문 답변
                </h3>
                <p className="text-[1.125rem] leading-[1.8] text-[#6B7280] mb-8">
                  지금 궁금할 만한 질문, AI가 먼저 생각합니다.
                  <br></br>
                  강의 맥락을 바탕으로 예상 질문을 제안하고, 답변까지 바로 제공합니다.
                </p>

                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      프롬프트 입력 없이, 질문과 답변을 즉시 확인
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      개념 정리와 이해를 돕는 다각도 설명
                    </span>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#639BEE] via-[#3B72DD] to-[#4D82E0] flex items-center justify-center flex-shrink-0 mt-1">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-[1.125rem] text-[#4B5563]">
                      질문·답변 히스토리 자동 저장
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
                <span
                  style={{
                    background:
                      "linear-gradient(135deg, #639BEE, #5B60A2, #83EAF1, #63A4FF, #3B72DD, #4D82E0)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                >
                  3단계
                </span>
                로 간단하게
              </h3>
              <p className="text-[1.125rem] text-[#6B7280] mb-16">
                복잡한 설정 없이 바로 시작할 수 있습니다
              </p>

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
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">강의 설정</h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      과목명을 입력하고 언어를 선택합니다.
                      <br></br>
                      관련 자료가 있다면 업로드할 수 있습니다.
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
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">실시간 전사</h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      강의가 시작되면 자동으로 음성을 인식하고
                      <br></br>
                      실시간으로 텍스트와 요약을 생성합니다.
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
                    <h4 className="text-xl font-bold text-[#1F2937] mb-3">원클릭 학습</h4>
                    <p className="text-[#6B7280] leading-relaxed">
                      궁금한 부분을 클릭하면<br></br>
                      관련 자료와 AI답변을 확인할 수 있습니다.
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
            지금 바로 시작하세요
          </h2>
          <p className="text-[1.125rem] leading-[1.6] text-white/90 mb-8 max-w-2xl mx-auto">
            무료로 시작하고 AI 학습 도우미의 강력한 기능을 경험해보세요
          </p>
          <Button
            size="lg"
            className="bg-white hover:bg-gray-50 rounded-lg px-8 py-6 h-auto shadow-lg hover:shadow-xl transition-all font-semibold"
            onClick={onLoginClick}
          >
            <span
              style={{
                background: "linear-gradient(135deg, #639BEE, #3B72DD, #4D82E0)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              지금 시작하기 →
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
    </div>
  );
}
