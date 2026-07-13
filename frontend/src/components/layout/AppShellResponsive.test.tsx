/**
 * AppShell responsive navigation tests (0052-F4).
 * Viewport CSS fidelity is covered by the browser journey.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

vi.mock("../chatbot/ChatbotWidget", () => ({
  ChatbotWidget: () => null,
}));

vi.mock("../ui/Toast", () => ({
  ToastContainer: () => null,
}));

vi.mock("../../store/auth", () => ({
  useAuthStore: () => ({
    user: { full_name: "Test User", email: "test@example.com" },
    logout: vi.fn(),
  }),
}));

vi.mock("../../store/ui", () => ({
  useUIStore: () => ({
    theme: "dark",
    sidebarCollapsed: false,
    chatbotOpen: false,
    toasts: [],
    setTheme: vi.fn(),
    toggleTheme: vi.fn(),
    toggleSidebar: vi.fn(),
    setSidebarCollapsed: vi.fn(),
    openChatbot: vi.fn(),
    closeChatbot: vi.fn(),
    toggleChatbot: vi.fn(),
    addToast: vi.fn(),
    removeToast: vi.fn(),
  }),
}));

import { AppShell } from "./AppShell";

function renderShell(initialPath = "/dashboard") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<div>Dashboard content</div>} />
          <Route path="/passport" element={<div>Passport content</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppShellResponsive", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("exposes open-navigation control wired to app-sidebar", () => {
    renderShell();
    const openBtn = screen.getByRole("button", { name: /open navigation/i });
    expect(openBtn).toHaveAttribute("aria-controls", "app-sidebar");
    expect(openBtn).toHaveAttribute("aria-expanded", "false");
    expect(document.querySelectorAll("#app-sidebar")).toHaveLength(1);
  });

  it("opens drawer, closes via backdrop, Escape, and navigation", () => {
    renderShell();
    const openBtn = screen.getByRole("button", { name: /open navigation/i });

    fireEvent.click(openBtn);
    expect(openBtn).toHaveAttribute("aria-expanded", "true");
    expect(
      screen.getByRole("button", { name: /close navigation/i }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /close navigation/i }));
    expect(openBtn).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(openBtn);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(openBtn).toHaveAttribute("aria-expanded", "false");

    fireEvent.click(openBtn);
    const passportLink = screen.getByRole("link", { name: /career passport/i });
    expect(passportLink).toHaveAttribute("href", "/passport");
    fireEvent.click(passportLink);
    expect(openBtn).toHaveAttribute("aria-expanded", "false");
  });

  it("keeps desktop collapse control available", () => {
    renderShell();
    expect(
      screen.getByRole("button", { name: /collapse sidebar|expand sidebar/i }),
    ).toBeInTheDocument();
  });
});
