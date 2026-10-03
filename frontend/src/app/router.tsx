import { createBrowserRouter, Navigate } from "react-router";
import LegacyApp from "@/legacy/App";
import { LandingRoute } from "@/legacy/routes/LandingRoute";
import { RequireAuth } from "./RequireAuth";

export const router = createBrowserRouter([
  {
    Component: LegacyApp,
    HydrateFallback: () => null,
    children: [
      { path: "/", Component: LandingRoute },
      {
        path: "/signup",
        lazy: async () => ({
          Component: (await import("@/features/auth/components/SignupPage")).SignupPage,
        }),
      },
      {
        Component: RequireAuth,
        children: [
          {
            path: "/lectures",
            lazy: async () => ({
              Component: (await import("@/legacy/routes/MainRoute")).MainRoute,
            }),
          },
          {
            path: "/lectures/:lectureId",
            lazy: async () => ({
              Component: (await import("@/legacy/routes/SessionRoute")).SessionRoute,
            }),
          },
          {
            path: "/settings",
            lazy: async () => ({
              Component: (await import("@/features/auth/components/SettingsPage")).SettingsPage,
            }),
          },
        ],
      },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
