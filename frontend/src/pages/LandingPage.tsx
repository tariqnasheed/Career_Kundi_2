/**
 * LandingPage.tsx
 * ================
 * Public marketing page. Glass cards, gradient mesh background, animated
 * headline, feature grid, testimonials, and dual CTA.
 */

import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Search, BookOpen, Map, Sparkles, Zap, Shield, BarChart2,
  ArrowRight, CheckCircle, Star,
} from "lucide-react";
import { useAuthStore } from "../store/auth";
import { Button } from "../components/ui/Button";

const FEATURES = [
  { icon: <Search size={22} />, title: "Smart Job Import", desc: "Paste any job URL and AI extracts the full posting — title, salary, skills — instantly.", color: "#06B6D4" },
  { icon: <BookOpen size={22} />, title: "Interview Pack Generator", desc: "Tailored interview questions, STAR answers, and technical prep in seconds.", color: "#8B5CF6" },
  { icon: <Sparkles size={22} />, title: "AI CV Builder", desc: "Build a standout CV from your profile. Preview across 10 templates. Export ATS-ready.", color: "#8B5CF6" },
  { icon: <Map size={22} />, title: "Career Roadmap", desc: "Personalised skill path with milestones and practice activities to reach your target role.", color: "#10B981" },
  { icon: <Zap size={22} />, title: "Auto Apply", desc: "Apply to compatible jobs with your CV and a generated cover letter — with your explicit confirmation.", color: "#F59E0B" },
  { icon: <BarChart2 size={22} />, title: "Progress & Badges", desc: "Earn meaningful badges as you practice, apply, and grow. Track your career momentum.", color: "#EC4899" },
];

const TESTIMONIALS = [
  { name: "Amara O.", role: "Software Engineer → Senior", text: "The roadmap showed me exactly what skills I was missing. I landed my senior role 4 months later.", stars: 5 },
  { name: "Tariq M.", role: "Career Changer", text: "I pasted a job URL and had a complete interview pack in under 2 minutes. The prep was incredibly specific.", stars: 5 },
  { name: "Priya S.", role: "Product Manager", text: "The CV Builder's template studio is genuinely impressive. I could see exactly how my CV would look before downloading.", stars: 5 },
];

export default function LandingPage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate("/dashboard", { replace: true });
  }, [isAuthenticated, navigate]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-base)", color: "var(--text-primary)" }}>
      {/* Nav */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 200,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0 2rem", height: "60px",
        background: "var(--bg-glass)", backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 700, fontFamily: "var(--font-heading)" }}>
          <Sparkles size={18} style={{ color: "var(--accent-violet)" }} />
          CareerKundi
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <Link to="/login" style={{ color: "var(--text-secondary)", textDecoration: "none", fontSize: "0.875rem" }}>Sign in</Link>
          <Link to="/register"><Button size="sm" variant="primary">Get started free</Button></Link>
        </div>
      </nav>

      {/* Hero */}
      <section style={{ paddingTop: "140px", paddingBottom: "80px", textAlign: "center", position: "relative", overflow: "hidden" }}>
        <div style={{
          position: "absolute", inset: 0, zIndex: 0,
          background: "var(--gradient-mesh)",
          pointerEvents: "none",
        }} />
        <motion.div
          style={{ position: "relative", zIndex: 1, maxWidth: "760px", margin: "0 auto", padding: "0 1.5rem" }}
          initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
        >
          <span style={{
            display: "inline-flex", alignItems: "center", gap: "6px",
            padding: "4px 14px", borderRadius: "9999px",
            border: "1px solid var(--border-default)",
            background: "rgba(139,92,246,0.1)", color: "var(--accent-violet-bright)",
            fontSize: "0.75rem", fontWeight: 600, marginBottom: "1.5rem",
          }}>
            <Sparkles size={12} /> AI-powered career acceleration
          </span>
          <h1 style={{
            fontFamily: "var(--font-heading)", fontSize: "clamp(2.4rem, 5vw, 3.8rem)",
            fontWeight: 800, lineHeight: 1.15, marginBottom: "1.25rem",
          }}>
            Your career, elevated by{" "}
            <span style={{ background: "var(--gradient-primary)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              agentic AI
            </span>
          </h1>
          <p style={{ fontSize: "1.15rem", color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: "2rem" }}>
            From job discovery to offer letter — CareerKundi's multi-agent AI handles the hard work.
            Tailored interview prep, smart CV building, career roadmaps, and guided applications.
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link to="/register"><Button size="lg" variant="primary" rightIcon={<ArrowRight size={18} />}>Start for free</Button></Link>
            <Link to="/login"><Button size="lg" variant="secondary">Sign in</Button></Link>
          </div>
          <div style={{ display: "flex", gap: "1.5rem", justifyContent: "center", flexWrap: "wrap", marginTop: "1.5rem" }}>
            {["No credit card required", "Works with any job posting", "Free tier available"].map(t => (
              <span key={t} style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                <CheckCircle size={13} style={{ color: "var(--accent-emerald)" }} /> {t}
              </span>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section style={{ padding: "60px 1.5rem", maxWidth: "1100px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <h2 style={{ fontFamily: "var(--font-heading)", fontSize: "2rem", fontWeight: 700, marginBottom: "0.75rem" }}>
            Everything your career needs
          </h2>
          <p style={{ color: "var(--text-secondary)" }}>Six AI-powered features, one unified platform.</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.5rem" }}>
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              style={{
                padding: "1.75rem", borderRadius: "16px",
                background: "var(--bg-glass)", backdropFilter: "blur(20px)",
                border: "1px solid var(--border-subtle)",
              }}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.07 }}
            >
              <div style={{
                width: "44px", height: "44px", borderRadius: "12px",
                background: `${f.color}18`, color: f.color,
                display: "flex", alignItems: "center", justifyContent: "center",
                marginBottom: "1rem",
              }}>{f.icon}</div>
              <h3 style={{ fontFamily: "var(--font-heading)", fontWeight: 600, marginBottom: "0.5rem" }}>{f.title}</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.65 }}>{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section style={{ padding: "60px 1.5rem", maxWidth: "1000px", margin: "0 auto" }}>
        <div style={{ textAlign: "center", marginBottom: "3rem" }}>
          <h2 style={{ fontFamily: "var(--font-heading)", fontSize: "2rem", fontWeight: 700 }}>Real results, real people</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.25rem" }}>
          {TESTIMONIALS.map((t, i) => (
            <motion.div
              key={t.name}
              style={{
                padding: "1.5rem", borderRadius: "16px",
                background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)",
              }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
            >
              <div style={{ display: "flex", gap: "2px", marginBottom: "0.75rem", color: "#F59E0B" }}>
                {Array.from({ length: t.stars }).map((_, si) => <Star key={si} size={13} fill="currentColor" />)}
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.65, marginBottom: "1rem" }}>
                "{t.text}"
              </p>
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{t.name}</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{t.role}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: "80px 1.5rem", textAlign: "center" }}>
        <motion.div
          style={{
            maxWidth: "600px", margin: "0 auto", padding: "3rem",
            borderRadius: "24px", background: "var(--gradient-primary-soft)",
            border: "1px solid var(--border-default)",
          }}
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
        >
          <h2 style={{ fontFamily: "var(--font-heading)", fontSize: "1.8rem", fontWeight: 700, marginBottom: "0.75rem" }}>
            Ready to accelerate your career?
          </h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.75rem" }}>
            Join thousands of professionals using AI to get ahead.
          </p>
          <Link to="/register">
            <Button size="lg" variant="primary" rightIcon={<ArrowRight size={18} />}>
              Get started — it's free
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: "1px solid var(--border-subtle)", padding: "1.5rem 2rem",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        flexWrap: "wrap", gap: "0.5rem",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontWeight: 700, fontFamily: "var(--font-heading)", fontSize: "0.875rem" }}>
          <Sparkles size={14} style={{ color: "var(--accent-violet)" }} /> CareerKundi
        </div>
        <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
          © {new Date().getFullYear()} CareerKundi. All rights reserved.
        </span>
      </footer>
    </div>
  );
}
