/**
 * components/layout/Sidebar.tsx
 * ==============================
 * Navigation sidebar with collapse/expand support.
 *
 * Groups:
 *   Main          – Dashboard, Job Search, Interview Pack
 *   Career Tools  – CV Builder, Career Roadmap
 *   Community     – Achievements/Badges
 *   Account       – Profile, Settings
 *
 * When collapsed (`sidebarCollapsed`), only icons are shown and tooltips
 * appear on hover (via CSS title attribute + aria-label).
 *
 * The chatbot FAB lives in AppShell, not here.
 */

import { NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Search,
  BookOpen,
  Map,
  Trophy,
  User,
  Settings,
  Layers,
  ChevronLeft,
  Sparkles,
} from "lucide-react";
import { clsx } from "clsx";
import { useUIStore } from "../../store/ui";
import styles from "./Sidebar.module.css";

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const NAV_GROUPS: { heading?: string; items: NavItem[] }[] = [
  {
    items: [
      { to: "/dashboard",      icon: <LayoutDashboard size={18} />, label: "Dashboard" },
      { to: "/jobs",           icon: <Search          size={18} />, label: "Jobs & Interview Prep" },
    ],
  },
  {
    heading: "Career Tools",
    items: [
      { to: "/cv-builder",     icon: <BookOpen        size={18} />, label: "CV Builder" },
      { to: "/roadmap",        icon: <Map             size={18} />, label: "Career Roadmap" },
      { to: "/platform",       icon: <Layers          size={18} />, label: "Platform" },
    ],
  },
  {
    heading: "Community",
    items: [
      { to: "/achievements",   icon: <Trophy          size={18} />, label: "Achievements" },
    ],
  },
  {
    heading: "Account",
    items: [
      { to: "/profile",        icon: <User            size={18} />, label: "Profile" },
      { to: "/settings",       icon: <Settings        size={18} />, label: "Settings" },
    ],
  },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <aside
      className={clsx(styles.sidebar, sidebarCollapsed && styles.collapsed)}
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div className={styles.brand}>
        <div className={styles.logo}>
          <Sparkles size={20} />
        </div>
        <AnimatePresence initial={false}>
          {!sidebarCollapsed && (
            <motion.span
              className={styles.brandName}
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.18 }}
            >
              CareerKundi
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav groups */}
      <nav className={styles.nav}>
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className={styles.group}>
            <AnimatePresence initial={false}>
              {group.heading && !sidebarCollapsed && (
                <motion.p
                  className={styles.groupHeading}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  {group.heading}
                </motion.p>
              )}
            </AnimatePresence>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  clsx(styles.navItem, isActive && styles.active)
                }
                title={sidebarCollapsed ? item.label : undefined}
                aria-label={item.label}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                <AnimatePresence initial={false}>
                  {!sidebarCollapsed && (
                    <motion.span
                      className={styles.navLabel}
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.18 }}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        className={styles.collapseBtn}
        onClick={toggleSidebar}
        aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <motion.span
          animate={{ rotate: sidebarCollapsed ? 180 : 0 }}
          transition={{ duration: 0.25 }}
          style={{ display: "flex" }}
        >
          <ChevronLeft size={16} />
        </motion.span>
        <AnimatePresence initial={false}>
          {!sidebarCollapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.18 }}
              style={{ overflow: "hidden", whiteSpace: "nowrap" }}
            >
              Collapse
            </motion.span>
          )}
        </AnimatePresence>
      </button>
    </aside>
  );
}
