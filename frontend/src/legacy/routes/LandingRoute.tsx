import { useNavigate } from "react-router";
import { LandingPage } from "../components/LandingPage";
import { useLegacyApp } from "../appContext";

export function LandingRoute() {
  const navigate = useNavigate();
  const { openLoginModal } = useLegacyApp();
  return <LandingPage onLoginClick={openLoginModal} onSignupClick={() => navigate("/signup")} />;
}
