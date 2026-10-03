import { useNavigate } from "react-router";
import { SignupPage } from "../components/SignupPage";
import { useLegacyApp } from "../appContext";

export function SignupRoute() {
  const navigate = useNavigate();
  const { handleSignup } = useLegacyApp();
  return <SignupPage onSignup={handleSignup} onBack={() => navigate("/")} />;
}
