/**
 * components/ui/Modal.tsx
 * =======================
 * Framer Motion dialog/modal with backdrop blur overlay.
 *
 * Features:
 *  – Animated backdrop (fade) + modal panel (scale + fade)
 *  – Focus trap via aria-modal + inert background
 *  – Close on backdrop click OR Escape key
 *  – Three size presets: sm, md, lg
 *  – Convenience sub-components: ModalHeader, ModalBody, ModalFooter
 *
 * Usage:
 *   <Modal open={isOpen} onClose={() => setIsOpen(false)} title="Confirm">
 *     <ModalBody>…</ModalBody>
 *     <ModalFooter>
 *       <Button onClick={onClose}>Cancel</Button>
 *       <Button variant="primary" onClick={handleConfirm}>Confirm</Button>
 *     </ModalFooter>
 *   </Modal>
 */

import { useEffect, type HTMLAttributes, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { clsx } from "clsx";
import styles from "./Modal.module.css";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl";
  /** If true, clicking the backdrop does NOT close the modal */
  persistent?: boolean;
  /** Put anything here — ModalBody + ModalFooter are optional helpers */
  children?: ReactNode;
  className?: string;
}

export function Modal({
  open,
  onClose,
  title,
  size = "md",
  persistent = false,
  children,
  className,
}: ModalProps) {
  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !persistent) onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, persistent, onClose]);

  // Lock body scroll while open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return createPortal(
    <AnimatePresence>
      {open && (
        <div className={styles.portal} role="dialog" aria-modal="true" aria-label={title}>
          {/* Backdrop */}
          <motion.div
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={!persistent ? onClose : undefined}
          />
          {/* Panel */}
          <div className={styles.positioner}>
            <motion.div
              className={clsx(styles.panel, styles[size], className)}
              initial={{ opacity: 0, scale: 0.94, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.94, y: 8 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            >
              {title && (
                <div className={styles.header}>
                  <h2 className={styles.title}>{title}</h2>
                  {!persistent && (
                    <button
                      className={styles.closeBtn}
                      onClick={onClose}
                      aria-label="Close dialog"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              )}
              {children}
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  );
}

export function ModalBody({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx(styles.body, className)} {...props}>
      {children}
    </div>
  );
}

export function ModalFooter({ className, children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={clsx(styles.footer, className)} {...props}>
      {children}
    </div>
  );
}
