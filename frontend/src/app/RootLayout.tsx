import { Outlet } from "react-router";
import { Toaster } from "@/shared/ui/sonner";

export function RootLayout() {
  return (
    <>
      <Outlet />
      <Toaster />
    </>
  );
}
