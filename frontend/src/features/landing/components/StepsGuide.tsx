import { Trans, useTranslation } from "react-i18next";
import { textGradientStyle } from "./textGradient";

const STEPS = [
  { titleKey: "landing.steps.step1Title", descKey: "landing.steps.step1Desc" },
  { titleKey: "landing.steps.step2Title", descKey: "landing.steps.step2Desc" },
  { titleKey: "landing.steps.step3Title", descKey: "landing.steps.step3Desc" },
] as const;

export function StepsGuide() {
  // Trans에 t를 넘겨야 언어가 바뀔 때 다시 그려짐. 넘기지 않으면 React Compiler가 이전 언어의 Trans를 재사용함
  const { t } = useTranslation();
  return (
    <div>
      <div className="text-center">
        <h3 className="text-[3rem] leading-[1.2] mb-4 text-[#1F2937]" style={{ fontWeight: 700 }}>
          <Trans
            t={t}
            i18nKey="landing.steps.title"
            components={{ highlight: <span style={textGradientStyle("var(--brand-gradient)")} /> }}
          />
        </h3>
        <p className="text-[1.125rem] text-[#6B7280] mb-16">{t("landing.steps.subtitle")}</p>

        <div className="grid md:grid-cols-3 gap-12 max-w-5xl mx-auto">
          {STEPS.map(({ titleKey, descKey }, i) => {
            const isLast = i === STEPS.length - 1;
            return (
              <div key={titleKey} className={isLast ? undefined : "relative"}>
                <div className="flex flex-col items-center">
                  <div className="w-24 h-24 rounded-full flex items-center justify-center mb-6 shadow-lg bg-brand-gradient">
                    <span className="text-white text-4xl font-bold">{i + 1}</span>
                  </div>
                  <h4 className="text-xl font-bold text-[#1F2937] mb-3">{t(titleKey)}</h4>
                  <p className="text-[#6B7280] leading-relaxed">
                    <Trans t={t} i18nKey={descKey} />
                  </p>
                </div>
                {/* 다음 단계로 이어지는 선 */}
                {!isLast && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#4D82E0] to-[#83EAF1]"></div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
