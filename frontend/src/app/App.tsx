import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router/dom";
import { useSyncUiLanguage } from "@/features/auth/hooks/useSyncUiLanguage";
import { BackendProvider } from "@/legacy/services/BackendContext";
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
      <BackendProvider>
        <RouterProvider router={router} />
      </BackendProvider>
    </QueryClientProvider>
  );
}
