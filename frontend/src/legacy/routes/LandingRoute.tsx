import { useState } from "react";
import { useNavigate } from "react-router";
import { LoginDialog } from "@/features/auth/components/LoginDialog";
import { LandingPage } from "../components/LandingPage";

export function LandingRoute() {
  const navigate = useNavigate();
  const [loginOpen, setLoginOpen] = useState(false);
  const goToSignup = () => navigate("/signup");
  return (
    <>
      <LandingPage onLoginClick={() => setLoginOpen(true)} onSignupClick={goToSignup} />
      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} onSignupClick={goToSignup} />
    </>
  );
}
