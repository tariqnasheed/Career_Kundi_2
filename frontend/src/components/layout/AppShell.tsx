/**
 * components/layout/AppShell.tsx
 * ================================
 * Root authenticated layout wrapper:
 *   [Sidebar] | [Header] + [main content] + [ChatbotWidget FAB]
 *
 * Desktop collapse uses the UI store. Mobile drawer state is local —
 * transient and not persisted.
 */

import { useCallback, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { clsx } from "clsx";
import { useUIStore } from "../../store/ui";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ChatbotWidget } from "../chatbot/ChatbotWidget";
import { ToastContainer } from "../ui/Toast";
import styles from "./AppShell.module.css";

export function AppShell() {
  const { sidebarCollapsed } = useUIStore();
  const location = useLocation();
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false);

  const closeMobileNavigation = useCallback(() => {
    setMobileNavigationOpen(false);
  }, []);

  const openMobileNavigation = useCallback(() => {
    setMobileNavigationOpen(true);
  }, []);

  // Close drawer on route change
  useEffect(() => {
    setMobileNavigationOpen(false);
  }, [location.pathname]);

  // Escape closes mobile drawer
  useEffect(() => {
    if (!mobileNavigationOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileNavigationOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNavigationOpen]);

  return (
    <div
      className={clsx(
        styles.shell,
        sidebarCollapsed && styles.sidebarCollapsed,
        mobileNavigationOpen && styles.mobileNavOpen,
      )}
    >
      <Sidebar
        mobileOpen={mobileNavigationOpen}
        onNavigate={closeMobileNavigation}
      />
      <div className={styles.main}>
        <Header
          mobileNavigationOpen={mobileNavigationOpen}
          onOpenNavigation={openMobileNavigation}
        />
        <main className={styles.content} id="main-content">
          <Outlet />
        </main>
      </div>
      {mobileNavigationOpen && (
        <button
          type="button"
          className={styles.mobileBackdrop}
          aria-label="Close navigation"
          onClick={closeMobileNavigation}
        />
      )}
      <ChatbotWidget />
      <ToastContainer />
    </div>
  );
}
