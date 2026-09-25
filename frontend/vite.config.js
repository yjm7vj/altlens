import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Point the dev proxy at a different backend port by setting
// VITE_PROXY_TARGET in frontend/.env.local (useful when 8000 is taken).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backend = env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: backend,
          changeOrigin: true,
        },
      },
    },
  };
});
