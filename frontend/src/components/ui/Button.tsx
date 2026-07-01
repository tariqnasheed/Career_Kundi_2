/**
 * components/ui/Button.tsx
 * ========================
 * Premium multi-variant button component. Variants:
 *   primary  — gradient fill (violet → cyan), the main CTA style
 *   secondary — glass surface with subtle border
 *   ghost    — transparent, minimal (for toolbar / icon-adjacent actions)
 *   danger   — rose fill for destructive actions
 *
 * Sizes: sm | md | lg
 * States: default, hover (lift + glow), active (press scale), loading, disabled
 *
 * The "glow sweep" hover effect uses a pseudo-element that slides a bright
 * highlight across the button surface — a signature Careerkundi micro-interaction.
 */

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";
import styles from "./Button.module.css";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "destructive";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      className,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const resolvedVariant = variant === "destructive" ? "danger" : variant;
    return (
      <button
        ref={ref}
        className={clsx(
          styles.button,
          styles[resolvedVariant],
          styles[size],
          fullWidth && styles.fullWidth,
          loading && styles.loading,
          className
        )}
        disabled={disabled || loading}
        aria-busy={loading}
        {...props}
      >
        {/* Glow sweep highlight — CSS-animated, pointer-events: none */}
        <span className={styles.glow} aria-hidden />

        {loading ? (
          <span className={styles.spinner} aria-hidden />
        ) : (
          leftIcon && <span className={styles.icon}>{leftIcon}</span>
        )}

        {children && <span className={styles.label}>{children}</span>}

        {!loading && rightIcon && <span className={styles.icon}>{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
