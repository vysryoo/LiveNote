import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { LoginDialog } from "@/features/auth/components/LoginDialog";
import { AppHeader, AppLogo } from "@/shared/components/AppHeader";
import { Button } from "@/shared/ui/button";
import { CtaSection } from "./CtaSection";
import { DemoVideoModal } from "./DemoVideoModal";
import { QnaFeature, ResourcesFeature, SummaryFeature } from "./FeatureSections";
import { HeroSection } from "./HeroSection";
import { StepsGuide } from "./StepsGuide";
import { textGradientStyle } from "./textGradient";

export function LandingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [showDemoModal, setShowDemoModal] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const openLogin = () => setLoginOpen(true);
  const goToSignup = () => navigate("/signup");

  return (
    <div className="min-h-screen bg-white">
      <AppHeader>
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <AppLogo />
          </div>

          <div className="flex" style={{ gap: "0.8em" }}>
            <Button
              variant="ghost"
              className="hover:bg-[#EEF2FF]"
              onClick={openLogin}
              style={textGradientStyle("linear-gradient(135deg, #639BEE, #3B72DD)")}
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
      </AppHeader>

      <HeroSection onStartClick={openLogin} onDemoClick={() => setShowDemoModal(true)} />

      <section className="py-24 px-8 bg-white">
        <div className="max-w-[1400px] mx-auto">
          <SummaryFeature />
          <ResourcesFeature />
          <QnaFeature />
          <StepsGuide />
        </div>
      </section>

      <CtaSection onStartClick={openLogin} />

      <DemoVideoModal isOpen={showDemoModal} onClose={() => setShowDemoModal(false)} />
      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} onSignupClick={goToSignup} />
    </div>
  );
}
