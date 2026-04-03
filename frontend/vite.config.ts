import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // Listen on all addresses
    strictPort: true,
    port: 5173,
    watch: {
      usePolling: true,
    },
    proxy: {
      // Forward /api requests to the FastAPI backend container
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
        secure: false,
      },
      // Forward /auth requests to the Keycloak container
      "/auth": {
        target: "http://keycloak:8080",
        changeOrigin: true,
        secure: false,
      },
      // Forward /mqtt WebSocket requests to HiveMQ
      "/mqtt": {
        target: "ws://hivemq:8081",
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/tests/setup.ts",
    css: true,
  },
  optimizeDeps: {
    include: ["latlon-geohash"],
  },
})
