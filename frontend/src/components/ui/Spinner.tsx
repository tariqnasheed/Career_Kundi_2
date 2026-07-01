/**
 * components/ui/Spinner.tsx
 * =========================
 * Accessible loading spinner.  Three sizes, two styles (ring / dots).
 * Ring style uses the brand violet accent; dots style uses the AI-think
 * animation from animations.css (three staggered pulsing dots).
 */

import { clsx } from "clsx";
import styles from "./Spinner.module.css";

export interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  variant?: "ring" | "dots";
  label?: string;
  className?: string;
}

export function Spinner({
  size = "md",
  variant = "ring",
  label = "Loading…",
  className,
}: SpinnerProps) {
  if (variant === "dots") {
    return (
      <span
        role="status"
        aria-label={label}
        className={clsx(styles.dots, styles[`dots-${size}`], className)}
      >
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className={styles.dot} />
        <span className="sr-only">{label}</span>
      </span>
    );
  }

  return (
    <span
      role="status"
      aria-label={label}
      className={clsx(styles.ring, styles[size], className)}
    >
      <span className="sr-only">{label}</span>
    </span>
  );
}
