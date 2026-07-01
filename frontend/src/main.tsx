/**
 * main.tsx – React entry point
 *
 * Mounts <App /> into #root, wraps it with:
 *   – QueryClientProvider (TanStack Query)
 *   – BrowserRouter (React Router)
 *
 * CSS is imported here so Vite includes it in the critical bundle.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./styles/globals.css";
import "./styles/animations.css";
import App from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30,        // 30s before a refetch
      retry: (failureCount, err: any) => {
        // Don't retry 4xx errors
        if (err?.response?.status >= 400 && err?.response?.status < 500) return false;
        return failureCount < 2;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

const root = document.getElementById("root");
if (!root) throw new Error("#root element not found in index.html");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);
