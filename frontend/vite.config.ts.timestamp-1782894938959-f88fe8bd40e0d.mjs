// vite.config.ts
import { defineConfig } from "file:///sessions/lucid-festive-hypatia/mnt/Career_Kundi_2/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///sessions/lucid-festive-hypatia/mnt/Career_Kundi_2/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
import { resolve } from "path";
var __vite_injected_original_dirname = "/sessions/lucid-festive-hypatia/mnt/Career_Kundi_2/frontend";
var vite_config_default = defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // "@/components/..." instead of "../../components/..." regardless of depth
      "@": resolve(__vite_injected_original_dirname, "src")
    }
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api requests to the FastAPI backend during local development.
      // Production traffic goes through the nginx reverse proxy configured in
      // /infra/nginx/ which routes /api → backend container, /* → this SPA.
      "/api": {
        target: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
        changeOrigin: true
      }
    }
  },
  build: {
    target: "es2020",
    outDir: "dist",
    sourcemap: false,
    // set to true when debugging production bundles
    rollupOptions: {
      output: {
        // Split vendor chunks to improve long-term caching: framework code
        // (react, framer-motion) and chart libs update far less often than
        // application code, so they get separate chunk hashes.
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          motion: ["framer-motion"],
          charts: ["recharts"],
          query: ["@tanstack/react-query"]
        }
      }
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    coverage: {
      reporter: ["text", "html"],
      exclude: ["node_modules/", "src/test-setup.ts"]
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCIvc2Vzc2lvbnMvbHVjaWQtZmVzdGl2ZS1oeXBhdGlhL21udC9DYXJlZXJfS3VuZGlfMi9mcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiL3Nlc3Npb25zL2x1Y2lkLWZlc3RpdmUtaHlwYXRpYS9tbnQvQ2FyZWVyX0t1bmRpXzIvZnJvbnRlbmQvdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL3Nlc3Npb25zL2x1Y2lkLWZlc3RpdmUtaHlwYXRpYS9tbnQvQ2FyZWVyX0t1bmRpXzIvZnJvbnRlbmQvdml0ZS5jb25maWcudHNcIjsvKipcbiAqIHZpdGUuY29uZmlnLnRzXG4gKiA9PT09PT09PT09PT09PVxuICogVml0ZSBidWlsZCBjb25maWd1cmF0aW9uIGZvciB0aGUgQ2FyZWVya3VuZGkgZnJvbnRlbmQuXG4gKlxuICogS2V5IGRlY2lzaW9uczpcbiAqICAtIEB2aXRlanMvcGx1Z2luLXJlYWN0IGZvciBmYXN0IFJlYWN0IEpTWCB0cmFuc2Zvcm0gKyBITVJcbiAqICAtIFBhdGggYWxpYXMgXCJAXCIgXHUyMTkyIFwic3JjL1wiIHNvIGltcG9ydHMgc3RheSBjbGVhbiByZWdhcmRsZXNzIG9mIG5lc3RpbmcgZGVwdGhcbiAqICAtIEFQSSBwcm94eSBpbiBkZXYgbW9kZSByb3V0ZXMgL2FwaS8qKiB0byB0aGUgRmFzdEFQSSBiYWNrZW5kIGF0IHBvcnQgODAwMCxcbiAqICAgIHNvIHRoZSBmcm9udGVuZCBkZXYgc2VydmVyIGFuZCB0aGUgYmFja2VuZCBzaGFyZSBhIHNpbmdsZSBvcmlnaW4gXHUyMDE0IG5vIENPUlNcbiAqICAgIGhlYWRlcnMgbmVlZGVkIGR1cmluZyBsb2NhbCBkZXZlbG9wbWVudC5cbiAqICAtIFRhcmdldCBlczIwMjAgZm9yIGEgZ29vZCBiYWxhbmNlIG9mIG1vZGVybiBzeW50YXggc3VwcG9ydCB2cyBjb21wYXRpYmlsaXR5LlxuICovXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tIFwidml0ZVwiO1xuaW1wb3J0IHJlYWN0IGZyb20gXCJAdml0ZWpzL3BsdWdpbi1yZWFjdFwiO1xuaW1wb3J0IHsgcmVzb2x2ZSB9IGZyb20gXCJwYXRoXCI7XG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtyZWFjdCgpXSxcblxuICByZXNvbHZlOiB7XG4gICAgYWxpYXM6IHtcbiAgICAgIC8vIFwiQC9jb21wb25lbnRzLy4uLlwiIGluc3RlYWQgb2YgXCIuLi8uLi9jb21wb25lbnRzLy4uLlwiIHJlZ2FyZGxlc3Mgb2YgZGVwdGhcbiAgICAgIFwiQFwiOiByZXNvbHZlKF9fZGlybmFtZSwgXCJzcmNcIiksXG4gICAgfSxcbiAgfSxcblxuICBzZXJ2ZXI6IHtcbiAgICBwb3J0OiA1MTczLFxuICAgIHByb3h5OiB7XG4gICAgICAvLyBQcm94eSBhbGwgL2FwaSByZXF1ZXN0cyB0byB0aGUgRmFzdEFQSSBiYWNrZW5kIGR1cmluZyBsb2NhbCBkZXZlbG9wbWVudC5cbiAgICAgIC8vIFByb2R1Y3Rpb24gdHJhZmZpYyBnb2VzIHRocm91Z2ggdGhlIG5naW54IHJldmVyc2UgcHJveHkgY29uZmlndXJlZCBpblxuICAgICAgLy8gL2luZnJhL25naW54LyB3aGljaCByb3V0ZXMgL2FwaSBcdTIxOTIgYmFja2VuZCBjb250YWluZXIsIC8qIFx1MjE5MiB0aGlzIFNQQS5cbiAgICAgIFwiL2FwaVwiOiB7XG4gICAgICAgIHRhcmdldDogcHJvY2Vzcy5lbnYuVklURV9BUElfQkFTRV9VUkwgPz8gXCJodHRwOi8vbG9jYWxob3N0OjgwMDBcIixcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgfSxcbiAgICB9LFxuICB9LFxuXG4gIGJ1aWxkOiB7XG4gICAgdGFyZ2V0OiBcImVzMjAyMFwiLFxuICAgIG91dERpcjogXCJkaXN0XCIsXG4gICAgc291cmNlbWFwOiBmYWxzZSwgLy8gc2V0IHRvIHRydWUgd2hlbiBkZWJ1Z2dpbmcgcHJvZHVjdGlvbiBidW5kbGVzXG4gICAgcm9sbHVwT3B0aW9uczoge1xuICAgICAgb3V0cHV0OiB7XG4gICAgICAgIC8vIFNwbGl0IHZlbmRvciBjaHVua3MgdG8gaW1wcm92ZSBsb25nLXRlcm0gY2FjaGluZzogZnJhbWV3b3JrIGNvZGVcbiAgICAgICAgLy8gKHJlYWN0LCBmcmFtZXItbW90aW9uKSBhbmQgY2hhcnQgbGlicyB1cGRhdGUgZmFyIGxlc3Mgb2Z0ZW4gdGhhblxuICAgICAgICAvLyBhcHBsaWNhdGlvbiBjb2RlLCBzbyB0aGV5IGdldCBzZXBhcmF0ZSBjaHVuayBoYXNoZXMuXG4gICAgICAgIG1hbnVhbENodW5rczoge1xuICAgICAgICAgIHZlbmRvcjogW1wicmVhY3RcIiwgXCJyZWFjdC1kb21cIiwgXCJyZWFjdC1yb3V0ZXItZG9tXCJdLFxuICAgICAgICAgIG1vdGlvbjogW1wiZnJhbWVyLW1vdGlvblwiXSxcbiAgICAgICAgICBjaGFydHM6IFtcInJlY2hhcnRzXCJdLFxuICAgICAgICAgIHF1ZXJ5OiBbXCJAdGFuc3RhY2svcmVhY3QtcXVlcnlcIl0sXG4gICAgICAgIH0sXG4gICAgICB9LFxuICAgIH0sXG4gIH0sXG5cbiAgdGVzdDoge1xuICAgIGVudmlyb25tZW50OiBcImpzZG9tXCIsXG4gICAgZ2xvYmFsczogdHJ1ZSxcbiAgICBzZXR1cEZpbGVzOiBbXCIuL3NyYy90ZXN0LXNldHVwLnRzXCJdLFxuICAgIGNvdmVyYWdlOiB7XG4gICAgICByZXBvcnRlcjogW1widGV4dFwiLCBcImh0bWxcIl0sXG4gICAgICBleGNsdWRlOiBbXCJub2RlX21vZHVsZXMvXCIsIFwic3JjL3Rlc3Qtc2V0dXAudHNcIl0sXG4gICAgfSxcbiAgfSxcbn0pO1xuIl0sCiAgIm1hcHBpbmdzIjogIjtBQWFBLFNBQVMsb0JBQW9CO0FBQzdCLE9BQU8sV0FBVztBQUNsQixTQUFTLGVBQWU7QUFmeEIsSUFBTSxtQ0FBbUM7QUFpQnpDLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVMsQ0FBQyxNQUFNLENBQUM7QUFBQSxFQUVqQixTQUFTO0FBQUEsSUFDUCxPQUFPO0FBQUE7QUFBQSxNQUVMLEtBQUssUUFBUSxrQ0FBVyxLQUFLO0FBQUEsSUFDL0I7QUFBQSxFQUNGO0FBQUEsRUFFQSxRQUFRO0FBQUEsSUFDTixNQUFNO0FBQUEsSUFDTixPQUFPO0FBQUE7QUFBQTtBQUFBO0FBQUEsTUFJTCxRQUFRO0FBQUEsUUFDTixRQUFRLFFBQVEsSUFBSSxxQkFBcUI7QUFBQSxRQUN6QyxjQUFjO0FBQUEsTUFDaEI7QUFBQSxJQUNGO0FBQUEsRUFDRjtBQUFBLEVBRUEsT0FBTztBQUFBLElBQ0wsUUFBUTtBQUFBLElBQ1IsUUFBUTtBQUFBLElBQ1IsV0FBVztBQUFBO0FBQUEsSUFDWCxlQUFlO0FBQUEsTUFDYixRQUFRO0FBQUE7QUFBQTtBQUFBO0FBQUEsUUFJTixjQUFjO0FBQUEsVUFDWixRQUFRLENBQUMsU0FBUyxhQUFhLGtCQUFrQjtBQUFBLFVBQ2pELFFBQVEsQ0FBQyxlQUFlO0FBQUEsVUFDeEIsUUFBUSxDQUFDLFVBQVU7QUFBQSxVQUNuQixPQUFPLENBQUMsdUJBQXVCO0FBQUEsUUFDakM7QUFBQSxNQUNGO0FBQUEsSUFDRjtBQUFBLEVBQ0Y7QUFBQSxFQUVBLE1BQU07QUFBQSxJQUNKLGFBQWE7QUFBQSxJQUNiLFNBQVM7QUFBQSxJQUNULFlBQVksQ0FBQyxxQkFBcUI7QUFBQSxJQUNsQyxVQUFVO0FBQUEsTUFDUixVQUFVLENBQUMsUUFBUSxNQUFNO0FBQUEsTUFDekIsU0FBUyxDQUFDLGlCQUFpQixtQkFBbUI7QUFBQSxJQUNoRDtBQUFBLEVBQ0Y7QUFDRixDQUFDOyIsCiAgIm5hbWVzIjogW10KfQo=
