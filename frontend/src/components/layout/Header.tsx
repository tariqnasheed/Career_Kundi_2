/**
 * components/layout/Header.tsx
 * =============================
 * Top bar: breadcrumb title, theme toggle, user avatar/menu.
 *
 * The breadcrumb is derived from the current pathname — each segment is
 * capitalised and the active segment is the page title.
 */

import { useLocation, Link } from "react-router-dom";
import { Sun, Moon, LogOut, User, Bell } from "lucide-react";
import { clsx } from "clsx";
import { useUIStore } from "../../store/ui";
import { useAuthStore } from "../../store/auth";
import styles from "./Header.module.css";

// Human-readable page title map
const PAGE_LABELS: Record<string, string> = {
  dashboard:      "Dashboard",
  jobs:           "Job Search",
  "interview-pack": "Interview Pack",
  "cv-builder":   "CV Builder",
  roadmap:        "Career Roadmap",
  achievements:   "Achievements",
  profile:        "Profile",
  settings:       "Settings",
};

function useBreadcrumb() {
  const { pathname } = useLocation();
  const segments = pathname.split("/").filter(Boolean);
  return segments.map((seg) => ({
    label: PAGE_LABELS[seg] ?? seg.replace(/-/g, " "),
    to: `/${segments.slice(0, segments.indexOf(seg) + 1).join("/")}`,
  }));
}

export function Header() {
  const { theme, toggleTheme } = useUIStore();
  const { user, logout }       = useAuthStore();
  const crumbs = useBreadcrumb();

  return (
    <header className={styles.header} role="banner">
      {/* Breadcrumb */}
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        {crumbs.map((crumb, i) => (
          <span key={crumb.to} className={styles.crumbGroup}>
            {i > 0 && <span className={styles.sep} aria-hidden>/</span>}
            {i < crumbs.length - 1 ? (
              <Link to={crumb.to} className={styles.crumbLink}>{crumb.label}</Link>
            ) : (
              <span className={styles.crumbActive} aria-current="page">{crumb.label}</span>
            )}
          </span>
        ))}
      </nav>

      {/* Right controls */}
      <div className={styles.controls}>
        {/* Notifications (placeholder — will be wired in Task #9) */}
        <button className={styles.iconBtn} aria-label="Notifications">
          <Bell size={18} />
        </button>

        {/* Theme toggle */}
        <button
          className={styles.iconBtn}
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User chip */}
        {user && (
          <div className={styles.userMenu}>
            <Link to="/profile" className={styles.avatar} aria-label="Your profile">
              {user.full_name
                ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
                : <User size={14} />}
            </Link>
            <button
              className={clsx(styles.iconBtn, styles.logoutBtn)}
              onClick={() => logout()}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
