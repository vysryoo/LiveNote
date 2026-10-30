import { useTranslation } from "react-i18next";
import ctaBackground from "@/assets/ctaBackground.webp";
import { Button } from "@/shared/ui/button";
import { textGradientStyle } from "./textGradient";

export function CtaSection({ onStartClick }: { onStartClick: () => void }) {
  const { t } = useTranslation();
  return (
    <section className="py-24 px-8 relative overflow-hidden">
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
          onClick={onStartClick}
        >
          <span style={textGradientStyle("linear-gradient(135deg, #639BEE, #3B72DD, #4D82E0)")}>
            {t("landing.startNow")}
          </span>
        </Button>

        <div className="mt-16 pt-8 border-t border-white/20">
          <p className="text-sm text-white/60">© 2025 LiveNote. All rights reserved.</p>
        </div>
      </div>
    </section>
  );
}
