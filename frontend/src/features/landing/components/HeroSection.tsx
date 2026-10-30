import { Trans, useTranslation } from "react-i18next";
import { Button } from "@/shared/ui/button";
import { GradientText } from "./GradientText";
import { textGradientStyle } from "./textGradient";

type HeroSectionProps = {
  onStartClick: () => void;
  onDemoClick: () => void;
};

export function HeroSection({ onStartClick, onDemoClick }: HeroSectionProps) {
  // Trans에 t를 넘겨야 언어가 바뀔 때 다시 그려짐. 넘기지 않으면 React Compiler가 이전 언어의 Trans를 재사용함
  const { t } = useTranslation();
  return (
    <section className="relative">
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
                onClick={onStartClick}
              >
                {t("landing.startNow")}
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-0 hover:bg-[#EEF2FF] rounded-lg w-[320px] h-[50px] text-lg bg-white"
                style={textGradientStyle("linear-gradient(135deg, #639BEE, #3B72DD)")}
                onClick={onDemoClick}
              >
                {t("landing.demoVideo")}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 배경 빛이 버튼 아래까지 퍼지도록 확보하는 공간 */}
      <div className="h-20 relative z-10" style={{ minHeight: "160px" }}></div>

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
  );
}
