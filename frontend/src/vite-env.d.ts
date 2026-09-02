/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin. Empty in development: the Vite proxy keeps it same-origin. */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
