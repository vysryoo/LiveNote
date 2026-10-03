import type { BackendPort } from "./ports";
import { createSpringBackend } from "./adapters/spring";
import { createSupabaseBackend } from "./adapters/supabase";

export type BackendType = "spring" | "supabase";

function getBackendType(): BackendType {
  return import.meta.env.VITE_BACKEND_TYPE ?? "spring";
}

export function createBackend(): BackendPort {
  const type = getBackendType();
  if (type === "supabase") return createSupabaseBackend();
  return createSpringBackend();
}
