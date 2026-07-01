/**
 * components/layout/AppShell.tsx
 * ================================
 * Root authenticated layout wrapper:
 *   [Sidebar] | [Header] + [main content] + [ChatbotWidget FAB]
 *
 * `sidebarCollapsed` from the UI store shrinks the sidebar to icon-only
 * mode and shifts the main area via a CSS custom property.
 *
 * ToastContainer is mounted here so notifications appear above all content.
 */

import { Outlet } from "react-router-dom";
import { clsx } from "clsx";
import { useUIStore } from "../../store/ui";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ChatbotWidget } from "../chatbot/ChatbotWidget";
import { ToastContainer } from "../ui/Toast";
import styles from "./AppShell.module.css";

export function AppShell() {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className={clsx(styles.shell, sidebarCollapsed && styles.sidebarCollapsed)}>
      <Sidebar />
      <div className={styles.main}>
        <Header />
        <main className={styles.content} id="main-content">
          <Outlet />
        </main>
      </div>
      <ChatbotWidget />
      <ToastContainer />
    </div>
  );
}
