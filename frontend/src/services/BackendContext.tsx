import React, { createContext, useContext, useMemo } from "react";
import type { BackendPort } from "./ports";
import { createBackend } from "./backend";

const BackendContext = createContext<BackendPort | null>(null);

export function BackendProvider({ children }: { children: any }) {
  const backend = useMemo(() => createBackend(), []);
  return <BackendContext.Provider value={backend}>{children}</BackendContext.Provider>;
}

export function useBackend(): BackendPort {
  const ctx = useContext(BackendContext);
  if (!ctx) throw new Error("useBackend must be used within BackendProvider");
  return ctx;
}


