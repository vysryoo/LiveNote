import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router/dom";
import { BackendProvider } from "@/legacy/services/BackendContext";
import { router } from "./router";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BackendProvider>
        <RouterProvider router={router} />
      </BackendProvider>
    </QueryClientProvider>
  );
}
