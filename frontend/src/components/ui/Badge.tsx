/**
 * components/ui/Badge.tsx
 * =======================
 * Small label chip for status indicators, skill tags, difficulty ratings,
 * intent labels, and category tags.
 *
 * Color presets map directly to the Careerkundi design token palette:
 *   violet   — primary brand (skills, features)
 *   cyan     — secondary (sources, categories)
 *   emerald  — success, completed, easy
 *   amber    — warning, in-progress, medium
 *   rose     — error, rejected, hard
 *   default  — neutral gray (generic tags)
 */

import { type HTMLAttributes } from "react";
import { clsx } from "clsx";
import styles from "./Badge.module.css";

export type BadgeColor = "default" | "violet" | "cyan" | "emerald" | "amber" | "rose" | "pink";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor;
  size?: "sm" | "md";
  dot?: boolean;  // show a colored dot prefix (status indicator)
}

export function Badge({
  color = "default",
  size = "md",
  dot = false,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={clsx(styles.badge, styles[color], styles[size], className)}
      {...props}
    >
      {dot && <span className={styles.dot} aria-hidden />}
      {children}
    </span>
  );
}
