import { createBrowserRouter, Navigate } from "react-router";
import LegacyApp from "@/legacy/App";
import { LandingRoute } from "@/legacy/routes/LandingRoute";
import { RequireAuth } from "@/legacy/routes/RequireAuth";

export const router = createBrowserRouter([
  {
    Component: LegacyApp,
    HydrateFallback: () => null,
    children: [
      { path: "/", Component: LandingRoute },
      {
        path: "/signup",
        lazy: async () => ({
          Component: (await import("@/legacy/routes/SignupRoute")).SignupRoute,
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
              Component: (await import("@/legacy/routes/SettingsRoute")).SettingsRoute,
            }),
          },
        ],
      },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
