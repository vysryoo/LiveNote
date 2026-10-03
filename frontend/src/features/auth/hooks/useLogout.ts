import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import { clearAuthToken } from "@/shared/lib/authToken";
import { authKeys } from "../api/authApi";

/**
 * 로그아웃 함수를 반환한다.
 *
 * 토큰과 서버 데이터 캐시를 모두 지우고 랜딩으로 이동한다. 백엔드에 로그아웃 API가 없어 서버 요청은 하지 않는다.
 *
 * @returns 로그아웃 함수
 */
export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { t } = useTranslation();

  return () => {
    clearAuthToken();
    queryClient.clear();
    queryClient.setQueryData(authKeys.me, null);
    navigate("/");
    // 비로그인 화면은 한국어로 표시되므로 안내도 한국어로 표시
    toast.success(t("auth.toast.logoutSuccess", { lng: "ko" }));
  };
}
