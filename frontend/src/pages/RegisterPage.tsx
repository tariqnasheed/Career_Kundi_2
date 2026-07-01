/**
 * RegisterPage.tsx
 * =================
 * Registration form with validation. Auto-logs in after success.
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, Mail, Lock, User, Eye, EyeOff, CheckCircle } from "lucide-react";
import { useAuthStore } from "../store/auth";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { useUIStore } from "../store/ui";

export default function RegisterPage() {
  const { register } = useAuthStore();
  const { addToast } = useUIStore();
  const navigate = useNavigate();

  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw]     = useState(false);
  const [loading, setLoading]   = useState(false);
  const [errors, setErrors]     = useState<Record<string, string>>({});

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!name.trim())          errs.name     = "Full name is required.";
    if (!email.includes("@")) errs.email    = "Enter a valid email address.";
    if (password.length < 8)  errs.password = "Password must be at least 8 characters.";
    return errs;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length) return;

    setLoading(true);
    try {
      await register(email, password, name);
      navigate("/dashboard", { replace: true });
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Registration failed. Please try again.";
      setErrors({ form: msg });
      addToast({ type: "error", message: msg });
    } finally {
      setLoading(false);
    }
  };

  const PERKS = [
    "Tailored interview prep in seconds",
    "AI CV builder with 10 templates",
    "Smart career roadmaps",
  ];

  return (
    <div style={{
      minHeight: "100vh", background: "var(--bg-base)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "1.5rem", position: "relative",
    }}>
      <div style={{ position: "absolute", inset: 0, background: "var(--gradient-mesh)", pointerEvents: "none" }} />
      <motion.div
        style={{
          width: "100%", maxWidth: "460px", position: "relative", zIndex: 1,
          background: "var(--bg-elevated)", borderRadius: "24px",
          border: "1px solid var(--border-default)", padding: "2.5rem",
          boxShadow: "var(--shadow-xl)",
        }}
        initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1.5rem", justifyContent: "center" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "var(--gradient-primary)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff" }}>
            <Sparkles size={18} />
          </div>
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.1rem" }}>CareerKundi</span>
        </div>

        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.4rem", textAlign: "center" }}>
          Create your account
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", textAlign: "center", marginBottom: "1.5rem" }}>
          Start your AI-powered career journey today
        </p>

        <div style={{ marginBottom: "1.5rem" }}>
          {PERKS.map(p => (
            <div key={p} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "6px" }}>
              <CheckCircle size={13} style={{ color: "var(--accent-emerald)", flexShrink: 0 }} /> {p}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
          <Input
            label="Full name"
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            leftIcon={<User size={15} />}
            placeholder="Tariq Nasheed"
            required
            fullWidth
            error={errors.name}
            autoComplete="name"
          />
          <Input
            label="Email address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            leftIcon={<Mail size={15} />}
            placeholder="you@example.com"
            required
            fullWidth
            error={errors.email}
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
            placeholder="At least 8 characters"
            required
            fullWidth
            hint="Minimum 8 characters"
            error={errors.password || errors.form}
            autoComplete="new-password"
          />

          <Button type="submit" variant="primary" fullWidth loading={loading} style={{ marginTop: "0.25rem" }}>
            Create account
          </Button>
        </form>

        <p style={{ textAlign: "center", fontSize: "0.875rem", color: "var(--text-secondary)", marginTop: "1.5rem" }}>
          Already have an account?{" "}
          <Link to="/login" style={{ color: "var(--accent-violet-bright)", textDecoration: "none", fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
