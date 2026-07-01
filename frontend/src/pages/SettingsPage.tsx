/**
 * SettingsPage.tsx
 * ================
 * Account settings: account info, notifications, data privacy, danger zone.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Settings, Bell, Shield, Trash2, Key, Moon, Sun, Monitor, ChevronDown, ChevronUp } from "lucide-react";
import { authApi, profileApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { useUIStore } from "../store/ui";
import { useAuthStore } from "../store/auth";

// ─── Section wrapper ────────────────────────────────────────────────────────
function SettingsSection({ icon, title, children, defaultOpen = true }: {
  icon: React.ReactNode; title: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card padding="none" style={{ marginBottom: "1.25rem", overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: "0.75rem",
          padding: "1rem 1.5rem", background: "none", border: "none", cursor: "pointer",
          borderBottom: open ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <span style={{ color: "var(--accent-violet)" }}>{icon}</span>
        <span style={{ fontWeight: 700, fontSize: "0.9rem", flex: 1, textAlign: "left" }}>{title}</span>
        {open ? <ChevronUp size={15} style={{ color: "var(--text-secondary)" }} /> : <ChevronDown size={15} style={{ color: "var(--text-secondary)" }} />}
      </button>
      {open && <div style={{ padding: "1.5rem" }}>{children}</div>}
    </Card>
  );
}

// ─── Toggle row ──────────────────────────────────────────────────────────────
function ToggleRow({ label, description, checked, onChange }: {
  label: string; description?: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: "1rem", cursor: "pointer", padding: "0.625rem 0", borderBottom: "1px solid var(--border-subtle)" }}>
      <div style={{ flex: 1 }}>
        <p style={{ fontWeight: 500, fontSize: "0.875rem" }}>{label}</p>
        {description && <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{description}</p>}
      </div>
      <div
        onClick={() => onChange(!checked)}
        style={{
          width: "42px", height: "24px", borderRadius: "999px",
          background: checked ? "var(--accent-violet)" : "var(--bg-overlay)",
          border: "1px solid var(--border-subtle)",
          position: "relative", cursor: "pointer", flexShrink: 0, transition: "background 0.2s",
        }}
      >
        <div style={{
          position: "absolute", top: "3px",
          left: checked ? "21px" : "3px",
          width: "16px", height: "16px", borderRadius: "50%",
          background: checked ? "#fff" : "var(--text-secondary)",
          transition: "left 0.2s",
        }} />
      </div>
    </label>
  );
}

// ─── Main page ──────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const { addToast } = useUIStore();
  const { logout, user } = useAuthStore();
  const qc = useQueryClient();
  const { theme, setTheme } = useUIStore();

  const [passwords, setPasswords] = useState({ current: "", new_: "", confirm: "" });
  const [notifications, setNotifications] = useState({
    badge_unlocked: true,
    job_match: true,
    weekly_summary: true,
    application_update: true,
  });

  const changePasswordMutation = useMutation({
    mutationFn: async () => {
      // Mock: real implementation calls PATCH /auth/password
      await new Promise(r => setTimeout(r, 800));
    },
    onSuccess: () => {
      setPasswords({ current: "", new_: "", confirm: "" });
      addToast({ type: "success", message: "Password changed successfully." });
    },
    onError: () => addToast({ type: "error", message: "Password change failed." }),
  });

  const handlePasswordSubmit = () => {
    if (passwords.new_ !== passwords.confirm) {
      addToast({ type: "error", message: "New passwords don't match." });
      return;
    }
    if (passwords.new_.length < 8) {
      addToast({ type: "error", message: "Password must be at least 8 characters." });
      return;
    }
    changePasswordMutation.mutate();
  };

  const THEMES = [
    { id: "system", label: "System", icon: <Monitor size={14} /> },
    { id: "dark",   label: "Dark",   icon: <Moon size={14} /> },
    { id: "light",  label: "Light",  icon: <Sun size={14} /> },
  ];

  return (
    <div style={{ padding: "2rem", maxWidth: "720px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.25rem" }}>Settings</h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", fontSize: "0.875rem" }}>Manage your account and application preferences.</p>

        {/* Account */}
        <SettingsSection icon={<Settings size={16} />} title="Account">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <Input label="Display name" value={user?.full_name ?? ""} readOnly fullWidth />
            <Input label="Email address" type="email" value={user?.email ?? ""} readOnly fullWidth hint="Contact support to change your email." />
          </div>
        </SettingsSection>

        {/* Appearance */}
        <SettingsSection icon={<Moon size={16} />} title="Appearance">
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>Choose how CareerKundi looks to you.</p>
          <div style={{ display: "flex", gap: "0.75rem" }}>
            {THEMES.map(t => (
              <button
                key={t.id}
                onClick={() => setTheme(t.id as any)}
                style={{
                  flex: 1, padding: "0.75rem 0.5rem", borderRadius: "10px",
                  border: theme === t.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                  background: theme === t.id ? "rgba(139,92,246,0.08)" : "transparent",
                  color: theme === t.id ? "var(--accent-violet)" : "var(--text-secondary)",
                  cursor: "pointer", fontSize: "0.8rem", fontWeight: theme === t.id ? 600 : 400,
                  display: "flex", flexDirection: "column", alignItems: "center", gap: "0.4rem",
                }}
              >
                {t.icon}{t.label}
              </button>
            ))}
          </div>
        </SettingsSection>

        {/* Notifications */}
        <SettingsSection icon={<Bell size={16} />} title="Notifications">
          <ToggleRow label="Badge unlocked" description="Celebrate when you earn a new achievement" checked={notifications.badge_unlocked} onChange={v => setNotifications(p => ({ ...p, badge_unlocked: v }))} />
          <ToggleRow label="Job match alerts" description="When a new job matches your profile" checked={notifications.job_match} onChange={v => setNotifications(p => ({ ...p, job_match: v }))} />
          <ToggleRow label="Weekly summary" description="A digest of your career progress" checked={notifications.weekly_summary} onChange={v => setNotifications(p => ({ ...p, weekly_summary: v }))} />
          <ToggleRow label="Application updates" description="Status changes on your applications" checked={notifications.application_update} onChange={v => setNotifications(p => ({ ...p, application_update: v }))} />
        </SettingsSection>

        {/* Security */}
        <SettingsSection icon={<Key size={16} />} title="Security" defaultOpen={false}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>Change your password. Use at least 8 characters including a number and a special character.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <Input label="Current password" type="password" value={passwords.current} onChange={e => setPasswords(p => ({ ...p, current: e.target.value }))} fullWidth />
            <Input label="New password" type="password" value={passwords.new_} onChange={e => setPasswords(p => ({ ...p, new_: e.target.value }))} fullWidth />
            <Input label="Confirm new password" type="password" value={passwords.confirm} onChange={e => setPasswords(p => ({ ...p, confirm: e.target.value }))} fullWidth />
            <Button variant="primary" onClick={handlePasswordSubmit} loading={changePasswordMutation.isPending} disabled={!passwords.current || !passwords.new_}>
              Change password
            </Button>
          </div>
        </SettingsSection>

        {/* Privacy */}
        <SettingsSection icon={<Shield size={16} />} title="Privacy & data" defaultOpen={false}>
          <div style={{ marginBottom: "1rem" }}>
            <p style={{ fontSize: "0.875rem", lineHeight: 1.65, color: "var(--text-secondary)" }}>
              CareerKundi stores your profile data and generated assets on our servers. We never sell your data
              to third parties. Auto-apply never stores passwords — the safety contract is enforced at the
              architecture level.
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={() => addToast({ type: "info", message: "Data export is being prepared. You'll receive it by email." })}>
            Export my data
          </Button>
        </SettingsSection>

        {/* Danger zone */}
        <SettingsSection icon={<Trash2 size={16} />} title="Danger zone" defaultOpen={false}>
          <div style={{
            padding: "1rem", borderRadius: "10px",
            background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.2)",
            marginBottom: "1rem",
          }}>
            <p style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--accent-rose)", marginBottom: "0.25rem" }}>Delete account</p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              This permanently deletes your account, all CVs, roadmaps, and application history.
              This cannot be undone.
            </p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            leftIcon={<Trash2 size={14} />}
            onClick={() => addToast({ type: "warning", title: "Action blocked", message: "Please contact support to delete your account." })}
          >
            Delete my account
          </Button>
        </SettingsSection>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button variant="ghost" onClick={() => logout()}>Sign out</Button>
        </div>
      </motion.div>
    </div>
  );
}
