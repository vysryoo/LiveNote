import { useTranslation } from "react-i18next";
import { Navigate, Outlet } from "react-router";
import { useMe } from "@/features/auth/hooks/useMe";

export function RequireAuth() {
  const { t } = useTranslation();
  const { data: user, isPending } = useMe();

  // 사용자 조회가 끝나기 전에 판정하면 새로고침 시 로그인 사용자도 랜딩으로 이동하므로 대기
  if (isPending) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        {t("common.loading")}
      </div>
    );
  }
  if (!user) return <Navigate to="/" replace />;
  return <Outlet />;
}
