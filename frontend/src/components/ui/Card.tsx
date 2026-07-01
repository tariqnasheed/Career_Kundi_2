/**
 * components/ui/Card.tsx
 * ======================
 * Glassmorphism card — the primary surface primitive in the Careerkundi UI.
 *
 * Variants:
 *   default  — glass surface with subtle border (bg-glass + backdrop-blur)
 *   elevated — opaque bg-elevated for content where transparency would hurt
 *              readability (tables, dense form sections)
 *   gradient — gradient border glow for highlighted/featured cards
 *
 * The `interactive` prop adds hover lift + glow + cursor: pointer for cards
 * that function as clickable items (job results, feature tiles, etc.).
 */

import { forwardRef, type HTMLAttributes } from "react";
import { clsx } from "clsx";
import styles from "./Card.module.css";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "gradient";
  interactive?: boolean;
  glow?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = "default",
      interactive = false,
      glow = false,
      padding = "md",
      className,
      children,
      ...props
    },
    ref
  ) => (
    <div
      ref={ref}
      className={clsx(
        styles.card,
        styles[variant],
        styles[`pad-${padding}`],
        interactive && styles.interactive,
        glow && styles.glow,
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);
Card.displayName = "Card";

/** Convenience sub-components for consistent card anatomy */
export const CardHeader = ({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.header, className)} {...props}>
    {children}
  </div>
);

export const CardTitle = ({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={clsx(styles.title, className)} {...props}>
    {children}
  </h3>
);

export const CardContent = ({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.content, className)} {...props}>
    {children}
  </div>
);

export const CardFooter = ({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx(styles.footer, className)} {...props}>
    {children}
  </div>
);
