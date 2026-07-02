/**
 * DashboardPage.tsx
 * ==================
 * Overview dashboard: stats, roadmap progress ring, recent badges,
 * quick-action tiles, and a recent jobs panel.
 */

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Search, BookOpen, Map, Sparkles, Trophy,
  ArrowRight, TrendingUp, FileText, Zap,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { jobApi, roadmapApi, badgeApi } from "../lib/api";

// ─── Quick-action tiles ───────────────────────────────────────────────────
const QUICK_ACTIONS = [
  { label: "Jobs & Interview Prep", icon: <Search size={20} />,   to: "/jobs",            color: "#06B6D4" },
  { label: "Build CV",           icon: <FileText size={20} />, to: "/cv-builder",      color: "#8B5CF6" },
  { label: "Career Roadmap",     icon: <Map size={20} />,      to: "/roadmap",         color: "#10B981" },
];

// ─── Progress ring ────────────────────────────────────────────────────────
function ProgressRing({ pct, size = 120, stroke = 10, color = "#8B5CF6" }: {
  pct: number; size?: number; stroke?: number; color?: string;
}) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border-subtle)" strokeWidth={stroke} />
      <motion.circle
        cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={color} strokeWidth={stroke}
        strokeDasharray={circ} strokeLinecap="round"
        initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: circ - dash }}
        transition={{ duration: 1.2, ease: "easeOut" }}
      />
    </svg>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────
function StatCard({ label, value, icon, color }: { label: string; value: number | string; icon: React.ReactNode; color: string }) {
  return (
    <Card padding="md">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: "0.25rem" }}>{label}</p>
          <p style={{ fontSize: "2rem", fontWeight: 700, fontFamily: "var(--font-heading)", color: "var(--text-primary)", lineHeight: 1 }}>{value}</p>
        </div>
        <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: `${color}1a`, color, display: "flex", alignItems: "center", justifyContent: "center" }}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();

  const { data: jobs    } = useQuery({ queryKey: ["jobs"],    queryFn: () => jobApi.list() });
  const { data: roadmaps } = useQuery({ queryKey: ["roadmaps"], queryFn: () => roadmapApi.list() });
  const { data: badgeStats } = useQuery({ queryKey: ["badge-stats"], queryFn: () => badgeApi.getStats() });
  const { data: pendingCelebrations } = useQuery({ queryKey: ["pending-celebrations"], queryFn: () => badgeApi.getPendingCelebrations() });

  const activeRoadmap = roadmaps?.find((r: any) => r.status === "active") || roadmaps?.[0];
  const roadmapPct = activeRoadmap
    ? Math.round((activeRoadmap.milestones?.filter((m: any) => m.status === "completed").length / (activeRoadmap.milestones?.length || 1)) * 100)
    : 0;

  const firstName = user?.full_name?.split(" ")[0] || "there";

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Greeting */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.35rem" }}>
          Good morning, {firstName} 👋
        </h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>Here's your career progress at a glance.</p>
      </motion.div>

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <StatCard label="Saved Jobs"    value={jobs?.length ?? 0}          icon={<Search size={20} />}   color="#06B6D4" />
        <StatCard label="Badges Earned" value={badgeStats?.total_earned ?? 0} icon={<Trophy size={20} />}  color="#F59E0B" />
        <StatCard label="Roadmap"       value={`${roadmapPct}%`}           icon={<TrendingUp size={20} />} color="#10B981" />
        <StatCard label="AI Assists"    value="∞"                          icon={<Sparkles size={20} />}  color="#8B5CF6" />
      </div>

      {/* Main grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Roadmap progress */}
        <Card padding="lg">
          <CardHeader><CardTitle>Career Roadmap</CardTitle></CardHeader>
          <CardContent>
            {activeRoadmap ? (
              <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
                <div style={{ position: "relative", flexShrink: 0 }}>
                  <ProgressRing pct={roadmapPct} />
                  <div style={{
                    position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center",
                  }}>
                    <span style={{ fontSize: "1.5rem", fontWeight: 700, fontFamily: "var(--font-heading)" }}>{roadmapPct}%</span>
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>complete</span>
                  </div>
                </div>
                <div>
                  <p style={{ fontWeight: 600, marginBottom: "0.4rem" }}>{activeRoadmap.target_role}</p>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    {activeRoadmap.milestones?.filter((m: any) => m.status === "completed").length || 0} of {activeRoadmap.milestones?.length || 0} milestones complete
                  </p>
                  <Link to="/roadmap" style={{ display: "inline-block", marginTop: "0.75rem" }}>
                    <Button size="sm" variant="secondary" rightIcon={<ArrowRight size={14} />}>View roadmap</Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "1.5rem 0" }}>
                <Map size={32} style={{ color: "var(--text-muted)", marginBottom: "0.75rem" }} />
                <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>No roadmap yet. Start building your career path.</p>
                <Link to="/roadmap"><Button size="sm" variant="primary">Create roadmap</Button></Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent badges */}
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Recent Achievements</CardTitle>
            <Link to="/achievements">
              <Button size="sm" variant="ghost" rightIcon={<ArrowRight size={14} />}>See all</Button>
            </Link>
          </CardHeader>
          <CardContent>
            {pendingCelebrations && pendingCelebrations.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {pendingCelebrations.slice(0, 3).map((ub: any) => (
                  <div key={ub.badge_id} style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                    <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "rgba(139,92,246,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Trophy size={16} style={{ color: "var(--accent-violet)" }} />
                    </div>
                    <div>
                      <p style={{ fontWeight: 600, fontSize: "0.875rem" }}>{ub.badge?.name}</p>
                      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{ub.badge?.category?.replace("_", " ")}</p>
                    </div>
                    <Badge color="violet" size="sm" style={{ marginLeft: "auto" }}>New!</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "1.5rem 0" }}>
                <Trophy size={28} style={{ color: "var(--text-muted)", marginBottom: "0.5rem" }} />
                <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Complete actions to earn badges and track your progress.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick actions */}
      <Card padding="lg" style={{ marginBottom: "1.5rem" }}>
        <CardHeader><CardTitle>Quick actions</CardTitle></CardHeader>
        <CardContent>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.75rem" }}>
            {QUICK_ACTIONS.map(({ label, icon, to, color }) => (
              <Link key={to} to={to} style={{ textDecoration: "none" }}>
                <motion.div
                  whileHover={{ y: -2 }}
                  style={{
                    padding: "1.25rem", borderRadius: "12px",
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-overlay)",
                    display: "flex", alignItems: "center", gap: "0.75rem",
                    cursor: "pointer", transition: "all 0.15s",
                  }}
                >
                  <div style={{ width: "38px", height: "38px", borderRadius: "10px", background: `${color}1a`, color, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    {icon}
                  </div>
                  <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)" }}>{label}</span>
                  <ArrowRight size={14} style={{ marginLeft: "auto", color: "var(--text-muted)" }} />
                </motion.div>
              </Link>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent jobs */}
      {jobs && jobs.length > 0 && (
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Recent saved jobs</CardTitle>
            <Link to="/jobs"><Button size="sm" variant="ghost" rightIcon={<ArrowRight size={14} />}>View all</Button></Link>
          </CardHeader>
          <CardContent>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {jobs.slice(0, 4).map((job: any) => (
                <div key={job.id} style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.75rem", borderRadius: "10px", background: "var(--bg-overlay)" }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontWeight: 600, fontSize: "0.875rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{job.title}</p>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{job.company_name} · {job.location}</p>
                  </div>
                  <Badge color={job.match_score >= 80 ? "emerald" : job.match_score >= 60 ? "amber" : "default"} size="sm">
                    {job.match_score ? `${Math.round(job.match_score)}% match` : "Saved"}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
