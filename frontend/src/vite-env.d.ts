/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_TYPE?: "spring" | "supabase";
  readonly VITE_API_URL?: string;
  readonly VITE_WS_URL?: string;
  readonly VITE_PUBLIC_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module "*.png" {
  const src: string;
  export default src;
}

declare module "*.jpg" {
  const src: string;
  export default src;
}

declare module "*.jpeg" {
  const src: string;
  export default src;
}

declare module "*.svg" {
  const src: string;
  export default src;
}

declare module "*.gif" {
  const src: string;
  export default src;
}

declare module "*.webp" {
  const src: string;
  export default src;
}
