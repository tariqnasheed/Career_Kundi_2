/**
 * store/ui.ts
 * ===========
 * Global UI state: theme, toast notifications, chatbot open/close, sidebar
 * collapsed state. Kept separate from auth store so theme changes don't
 * trigger re-renders of auth-dependent components.
 */

import { create } from "zustand";

type Theme = "dark" | "light";

export interface Toast {
  id: string;
  type: "success" | "error" | "info" | "warning" | "ai";
  title?: string;
  message: string;
  duration?: number;  // ms, default 4000
}

interface UIState {
  theme: Theme;
  sidebarCollapsed: boolean;
  chatbotOpen: boolean;
  toasts: Toast[];

  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  openChatbot: () => void;
  closeChatbot: () => void;
  toggleChatbot: () => void;
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

const storedTheme = (localStorage.getItem("ck_theme") as Theme | null) ?? "dark";

// Apply initial theme to <html> element so there's no flash before React mounts
document.documentElement.setAttribute("data-theme", storedTheme);

export const useUIStore = create<UIState>((set, get) => ({
  theme: storedTheme,
  sidebarCollapsed: false,
  chatbotOpen: false,
  toasts: [],

  setTheme: (theme) => {
    localStorage.setItem("ck_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
    set({ theme });
  },

  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    get().setTheme(next);
  },

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  openChatbot: () => set({ chatbotOpen: true }),
  closeChatbot: () => set({ chatbotOpen: false }),
  toggleChatbot: () => set((s) => ({ chatbotOpen: !s.chatbotOpen })),

  addToast: (toast) => {
    const id = Math.random().toString(36).slice(2);
    const duration = toast.duration ?? 4_000;
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
    // Auto-dismiss after duration
    setTimeout(() => get().removeToast(id), duration);
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
