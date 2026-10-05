import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router/dom";
import { useSyncUiLanguage } from "@/features/auth/hooks/useSyncUiLanguage";
import { router } from "./router";

const queryClient = new QueryClient();

function UiLanguageSync() {
  useSyncUiLanguage();
  return null;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <UiLanguageSync />
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
