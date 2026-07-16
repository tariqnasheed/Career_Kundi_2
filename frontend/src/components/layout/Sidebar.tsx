/**
 * components/layout/Sidebar.tsx
 * ==============================
 * Navigation sidebar with collapse/expand and mobile drawer support.
 */

import { NavLink } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Search,
  BookOpen,
  BookUser,
  Map,
  Trophy,
  User,
  Settings,
  Layers,
  Library,
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

interface SidebarProps {
  mobileOpen?: boolean;
  onNavigate?: () => void;
}

const NAV_GROUPS: { heading?: string; items: NavItem[] }[] = [
  {
    items: [
      { to: "/dashboard", icon: <LayoutDashboard size={18} />, label: "Dashboard" },
      { to: "/jobs", icon: <Search size={18} />, label: "Jobs & Interview Prep" },
    ],
  },
  {
    heading: "Career Tools",
    items: [
      { to: "/passport", icon: <BookUser size={18} />, label: "Career Passport" },
      { to: "/evidence", icon: <Library size={18} />, label: "Evidence Library" },
      { to: "/cv-builder", icon: <BookOpen size={18} />, label: "CV Builder" },
      { to: "/roadmap", icon: <Map size={18} />, label: "Career Roadmap" },
      { to: "/platform", icon: <Layers size={18} />, label: "Platform" },
    ],
  },
  {
    heading: "Community",
    items: [
      { to: "/achievements", icon: <Trophy size={18} />, label: "Achievements" },
    ],
  },
  {
    heading: "Account",
    items: [
      { to: "/profile", icon: <User size={18} />, label: "Profile" },
      { to: "/settings", icon: <Settings size={18} />, label: "Settings" },
    ],
  },
];

export function Sidebar({ mobileOpen = false, onNavigate }: SidebarProps) {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  // Mobile drawer always shows labels; desktop respects collapse store.
  const showLabels = mobileOpen || !sidebarCollapsed;

  return (
    <aside
      id="app-sidebar"
      className={clsx(
        styles.sidebar,
        sidebarCollapsed && styles.collapsed,
        mobileOpen && styles.mobileOpen,
      )}
      aria-label="Main navigation"
    >
      <div className={styles.brand}>
        <div className={styles.logo} aria-hidden="true">
          <Sparkles size={20} />
        </div>
        <AnimatePresence initial={false}>
          {showLabels && (
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

      <nav className={styles.nav}>
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className={styles.group}>
            <AnimatePresence initial={false}>
              {group.heading && showLabels && (
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
                title={!showLabels ? item.label : undefined}
                aria-label={item.label}
                onClick={() => onNavigate?.()}
              >
                <span className={styles.navIcon} aria-hidden="true">
                  {item.icon}
                </span>
                <AnimatePresence initial={false}>
                  {showLabels && (
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

      <button
        type="button"
        className={styles.collapseBtn}
        onClick={toggleSidebar}
        aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <motion.span
          animate={{ rotate: sidebarCollapsed ? 180 : 0 }}
          transition={{ duration: 0.25 }}
          style={{ display: "flex" }}
          aria-hidden="true"
        >
          <ChevronLeft size={16} />
        </motion.span>
        <AnimatePresence initial={false}>
          {showLabels && (
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
