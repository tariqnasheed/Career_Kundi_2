/**
 * components/layout/Header.tsx
 * =============================
 * Top bar: mobile menu, breadcrumb title, theme toggle, user avatar/menu.
 */

import { useLocation, Link } from "react-router-dom";
import { Sun, Moon, LogOut, User, Bell, Menu } from "lucide-react";
import { clsx } from "clsx";
import { useUIStore } from "../../store/ui";
import { useAuthStore } from "../../store/auth";
import styles from "./Header.module.css";

const PAGE_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  jobs: "Jobs & Interview Prep",
  "cv-builder": "CV Builder",
  roadmap: "Career Roadmap",
  achievements: "Achievements",
  profile: "Profile",
  settings: "Settings",
  platform: "Platform Foundation",
  passport: "Career Passport",
};

interface HeaderProps {
  mobileNavigationOpen?: boolean;
  onOpenNavigation?: () => void;
}

function useBreadcrumb() {
  const { pathname } = useLocation();
  const segments = pathname.split("/").filter(Boolean);
  return segments.map((seg) => ({
    label: PAGE_LABELS[seg] ?? seg.replace(/-/g, " "),
    to: `/${segments.slice(0, segments.indexOf(seg) + 1).join("/")}`,
  }));
}

export function Header({
  mobileNavigationOpen = false,
  onOpenNavigation,
}: HeaderProps) {
  const { theme, toggleTheme } = useUIStore();
  const { user, logout } = useAuthStore();
  const crumbs = useBreadcrumb();

  return (
    <header className={styles.header} role="banner">
      <div className={styles.leading}>
        <button
          type="button"
          className={clsx(styles.iconBtn, styles.menuBtn)}
          aria-label="Open navigation"
          aria-controls="app-sidebar"
          aria-expanded={mobileNavigationOpen}
          onClick={onOpenNavigation}
        >
          <Menu size={18} aria-hidden="true" />
        </button>

        <nav className={styles.breadcrumb} aria-label="Breadcrumb">
          {crumbs.map((crumb, i) => (
            <span key={crumb.to} className={styles.crumbGroup}>
              {i > 0 && (
                <span className={styles.sep} aria-hidden="true">
                  /
                </span>
              )}
              {i < crumbs.length - 1 ? (
                <Link to={crumb.to} className={styles.crumbLink}>
                  {crumb.label}
                </Link>
              ) : (
                <span className={styles.crumbActive} aria-current="page">
                  {crumb.label}
                </span>
              )}
            </span>
          ))}
        </nav>
      </div>

      <div className={styles.controls}>
        <button
          type="button"
          className={clsx(styles.iconBtn, styles.notifyBtn)}
          aria-label="Notifications"
        >
          <Bell size={18} aria-hidden="true" />
        </button>

        <button
          type="button"
          className={styles.iconBtn}
          onClick={toggleTheme}
          aria-label={
            theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
          }
        >
          {theme === "dark" ? (
            <Sun size={18} aria-hidden="true" />
          ) : (
            <Moon size={18} aria-hidden="true" />
          )}
        </button>

        {user && (
          <div className={styles.userMenu}>
            <Link to="/profile" className={styles.avatar} aria-label="Your profile">
              {user.full_name
                ? user.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()
                : <User size={14} aria-hidden="true" />}
            </Link>
            <button
              type="button"
              className={clsx(styles.iconBtn, styles.logoutBtn)}
              onClick={() => logout()}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={16} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
