/**
 * vite.config.ts
 * ==============
 * Vite build configuration for the Careerkundi frontend.
 *
 * Key decisions:
 *  - @vitejs/plugin-react for fast React JSX transform + HMR
 *  - Path alias "@" → "src/" so imports stay clean regardless of nesting depth
 *  - API proxy in dev mode routes /api/** to the FastAPI backend at port 8000,
 *    so the frontend dev server and the backend share a single origin — no CORS
 *    headers needed during local development.
 *  - Target es2020 for a good balance of modern syntax support vs compatibility.
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      // "@/components/..." instead of "../../components/..." regardless of depth
      "@": resolve(__dirname, "src"),
    },
  },

  server: {
    port: 5173,
    proxy: {
      // Proxy all /api requests to the FastAPI backend during local development.
      // Production traffic goes through the nginx reverse proxy configured in
      // /infra/nginx/ which routes /api → backend container, /* → this SPA.
      "/api": {
        target: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
        changeOrigin: true,
        // Interview-pack generation on a local LLM can take minutes; keep the
        // dev proxy from cutting the request off before the backend responds.
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },

  build: {
    target: "es2020",
    outDir: "dist",
    sourcemap: false, // set to true when debugging production bundles
    rollupOptions: {
      output: {
        // Split vendor chunks to improve long-term caching: framework code
        // (react, framer-motion) and chart libs update far less often than
        // application code, so they get separate chunk hashes.
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          motion: ["framer-motion"],
          charts: ["recharts"],
          query: ["@tanstack/react-query"],
        },
      },
    },
  },

  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    coverage: {
      reporter: ["text", "html"],
      exclude: ["node_modules/", "src/test-setup.ts"],
    },
  },
});
