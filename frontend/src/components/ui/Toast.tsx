/**
 * components/ui/Toast.tsx
 * =======================
 * Toast notification renderer.  This component reads from the ui Zustand
 * store and renders the active toasts in a fixed portal at the bottom-right
 * corner. It is mounted once in AppShell so it appears on every page.
 *
 * Toast variants map to platform event semantics:
 *   success  – action completed, resource saved, pipeline done
 *   error    – API error, validation failure, pipeline rejected
 *   warning  – soft warning (low confidence, partial result)
 *   info     – neutral notification (new session, remember, etc.)
 *   ai       – AI pipeline update (uses violet accent + dots spinner)
 */

import { useEffect } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";
import { clsx } from "clsx";
import { useUIStore, type Toast } from "../../store/ui";
import { Spinner } from "./Spinner";
import styles from "./Toast.module.css";

const ICON: Record<Toast["type"], React.ReactNode> = {
  success: <CheckCircle  size={16} />,
  error:   <XCircle     size={16} />,
  warning: <AlertTriangle size={16} />,
  info:    <Info         size={16} />,
  ai:      <Spinner variant="dots" size="sm" label="" />,
};

export function ToastContainer() {
  const { toasts, removeToast } = useUIStore();

  return createPortal(
    <div className={styles.container} aria-live="polite" aria-atomic="false">
      <AnimatePresence initial={false}>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
        ))}
      </AnimatePresence>
    </div>,
    document.body
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const duration = toast.duration ?? 4500;

  useEffect(() => {
    if (duration <= 0) return;
    const t = setTimeout(onDismiss, duration);
    return () => clearTimeout(t);
  }, [duration, onDismiss]);

  return (
    <motion.div
      layout
      role="alert"
      className={clsx(styles.toast, styles[toast.type])}
      initial={{ opacity: 0, x: 48, scale: 0.92 }}
      animate={{ opacity: 1, x: 0,  scale: 1 }}
      exit={{    opacity: 0, x: 48, scale: 0.92 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
    >
      <span className={styles.icon}>{ICON[toast.type]}</span>
      <div className={styles.body}>
        {toast.title && <p className={styles.title}>{toast.title}</p>}
        <p className={styles.message}>{toast.message}</p>
      </div>
      <button
        className={styles.dismiss}
        onClick={onDismiss}
        aria-label="Dismiss notification"
      >
        <X size={14} />
      </button>
    </motion.div>
  );
}
