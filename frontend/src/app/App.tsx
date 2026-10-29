import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { RouterProvider } from "react-router/dom";
import { authKeys } from "@/features/auth/api/authApi";
import { useSyncUiLanguage } from "@/features/auth/hooks/useSyncUiLanguage";
import { onSessionExpired } from "@/shared/lib/http";
import { router } from "./router";

const queryClient = new QueryClient();

function UiLanguageSync() {
  useSyncUiLanguage();
  return null;
}

// 토큰 갱신에 실패하면 비로그인 상태로 바꿔 로그인이 필요한 화면에서 랜딩으로 이동시킴
function SessionExpiryHandler() {
  const queryClient = useQueryClient();
  useEffect(
    () => onSessionExpired(() => queryClient.setQueryData(authKeys.me, null)),
    [queryClient],
  );
  return null;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <UiLanguageSync />
      <SessionExpiryHandler />
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
