import { Navigate, Outlet, useOutletContext } from "react-router";
import { useLegacyApp } from "../appContext";

// 로그인 확인이 끝나기 전에 판정하면 새로고침 시 로그인 사용자도 랜딩으로 튕기므로 대기
export function RequireAuth() {
  const app = useLegacyApp();
  const context = useOutletContext();

  if (app.initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        초기화 중입니다...
      </div>
    );
  }
  if (!app.user) return <Navigate to="/" replace />;
  return <Outlet context={context} />;
}
