/**
 * LoginPage.tsx
 * ==============
 * Email + password sign-in. Shows error toast on failure.
 * Redirects to /dashboard on success.
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, Eye, EyeOff } from "lucide-react";
import { useAuthStore } from "../store/auth";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useUIStore } from "../store/ui";

export default function LoginPage() {
  const { login } = useAuthStore();
  const { addToast } = useUIStore();
  const navigate = useNavigate();

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Invalid email or password.";
      setError(msg);
      addToast({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", background: "var(--bg-base)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "1.5rem", position: "relative",
    }}>
      <div style={{
        position: "absolute", inset: 0, background: "var(--gradient-mesh)", pointerEvents: "none",
      }} />
      <motion.div
        style={{
          width: "100%", maxWidth: "420px", position: "relative", zIndex: 1,
          background: "var(--bg-elevated)", borderRadius: "24px",
          border: "1px solid var(--border-default)", padding: "2.5rem",
          boxShadow: "var(--shadow-xl)",
        }}
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "2rem", justifyContent: "center" }}>
          <div style={{
            width: "36px", height: "36px", borderRadius: "10px",
            background: "var(--gradient-primary)",
            display: "flex", alignItems: "center", justifyContent: "center", color: "#fff",
          }}>
            <Sparkles size={18} />
          </div>
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.1rem" }}>CareerKundi</span>
        </div>

        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem", textAlign: "center" }}>
          Welcome back
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", textAlign: "center", marginBottom: "2rem" }}>
          Sign in to continue your career journey
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <Input
            label="Email address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            leftIcon={<Mail size={15} />}
            placeholder="you@example.com"
            required
            fullWidth
            autoComplete="email"
          />
          <Input
            label="Password"
            type={showPw ? "text" : "password"}
            value={password}
            onChange={e => setPassword(e.target.value)}
            leftIcon={<Lock size={15} />}
            rightIcon={
              <button type="button" onClick={() => setShowPw(!showPw)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", display: "flex" }}>
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            }
            placeholder="Your password"
            required
            fullWidth
            autoComplete="current-password"
            error={error || undefined}
          />

          <Button type="submit" variant="primary" fullWidth loading={loading}>
            Sign in
          </Button>
        </form>

        <p style={{ textAlign: "center", fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "1.5rem" }}>
          Don't have an account?{" "}
          <Link to="/register" style={{ color: "var(--accent-violet-bright)", textDecoration: "none", fontWeight: 600 }}>
            Create one free
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
