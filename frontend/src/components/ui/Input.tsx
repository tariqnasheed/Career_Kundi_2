/**
 * components/ui/Input.tsx
 * =======================
 * Styled text input + textarea components that fit the glass aesthetic.
 * Label, hint text, and error message are all rendered as part of the
 * component so the surrounding form code stays clean.
 *
 * The focus state uses the brand violet accent with a subtle glow ring —
 * the same visual language as the button's primary variant.
 */

import { forwardRef, type InputHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { clsx } from "clsx";
import styles from "./Input.module.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, hint, error, leftIcon, rightIcon, fullWidth, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className={clsx(styles.wrapper, fullWidth && styles.fullWidth)}>
        {label && (
          <label className={styles.label} htmlFor={inputId}>
            {label}
          </label>
        )}
        <div className={clsx(styles.inputWrap, error && styles.hasError)}>
          {leftIcon && <span className={styles.iconLeft} aria-hidden>{leftIcon}</span>}
          <input
            ref={ref}
            id={inputId}
            className={clsx(styles.input, leftIcon && styles.withLeftIcon, rightIcon && styles.withRightIcon, className)}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            aria-invalid={!!error}
            {...props}
          />
          {rightIcon && <span className={styles.iconRight} aria-hidden>{rightIcon}</span>}
        </div>
        {hint && !error && <p id={`${inputId}-hint`} className={styles.hint}>{hint}</p>}
        {error && <p id={`${inputId}-error`} role="alert" className={styles.error}>{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
  fullWidth?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, hint, error, fullWidth, className, id, rows = 4, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className={clsx(styles.wrapper, fullWidth && styles.fullWidth)}>
        {label && <label className={styles.label} htmlFor={inputId}>{label}</label>}
        <textarea
          ref={ref}
          id={inputId}
          rows={rows}
          className={clsx(styles.input, styles.textarea, error && styles.hasError, className)}
          aria-invalid={!!error}
          {...props}
        />
        {hint && !error && <p className={styles.hint}>{hint}</p>}
        {error && <p role="alert" className={styles.error}>{error}</p>}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";
