import { createBrowserRouter, Navigate } from "react-router";
import { LandingPage } from "@/features/landing/components/LandingPage";
import { RequireAuth } from "./RequireAuth";
import { RootLayout } from "./RootLayout";

export const router = createBrowserRouter([
  {
    Component: RootLayout,
    HydrateFallback: () => null,
    children: [
      { path: "/", Component: LandingPage },
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
              Component: (await import("@/features/lectures/components/LectureListPage"))
                .LectureListPage,
            }),
          },
          {
            path: "/lectures/:lectureId",
            lazy: async () => ({
              Component: (await import("@/features/session/components/SessionPage")).SessionPage,
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
