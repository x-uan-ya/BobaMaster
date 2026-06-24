/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_WS_URL?: string
  readonly VITE_SHOP_ID?: string
  readonly VITE_STORE_NAME?: string
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
