/**
 * AchievementsPage.tsx
 * =====================
 * Badge gallery with locked/unlocked states, celebration animations,
 * rarity levels, category filters, and overall progress tracking.
 */

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Trophy, Star, Zap, Lock, CheckCircle, Filter, TrendingUp } from "lucide-react";
import { badgeApi } from "../lib/api";
import { Badge as BadgeChip } from "../components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";

// ─── Types ──────────────────────────────────────────────────────────────────

interface BadgeDef {
  id: string; name: string; description: string; category: string;
  icon: string; color_swatch: string; rarity: string;
}
interface UserBadge {
  badge_id: string; progress: number; is_earned: boolean;
  earned_at: string | null; celebration_shown: boolean; pct_complete: number;
  badge: BadgeDef;
}

// ─── Constants ──────────────────────────────────────────────────────────────

const RARITY_STYLES: Record<string, { label: string; color: string; glow: string }> = {
  common:    { label: "Common",    color: "#9CA3AF", glow: "0 0 0 transparent" },
  uncommon:  { label: "Uncommon",  color: "#10B981", glow: "0 0 12px rgba(16,185,129,0.35)" },
  rare:      { label: "Rare",      color: "#3B82F6", glow: "0 0 16px rgba(59,130,246,0.45)" },
  epic:      { label: "Epic",      color: "#8B5CF6", glow: "0 0 20px rgba(139,92,246,0.5)" },
  legendary: { label: "Legendary", color: "#F59E0B", glow: "0 0 28px rgba(245,158,11,0.6)" },
};

const CATEGORIES = [
  { id: "all",          label: "All badges" },
  { id: "cv_builder",   label: "CV Builder" },
  { id: "job_search",   label: "Job Search" },
  { id: "roadmap",      label: "Roadmap" },
  { id: "interview",    label: "Interview" },
  { id: "learning",     label: "Learning" },
  { id: "streak",       label: "Streaks" },
  { id: "milestone",    label: "Milestones" },
  { id: "legendary_cat",label: "Legendary" },
];

// ─── Celebration overlay ────────────────────────────────────────────────────

function CelebrationOverlay({ badge, onDone }: { badge: UserBadge; onDone: () => void }) {
  const rarity = RARITY_STYLES[badge.badge.rarity] ?? RARITY_STYLES.common;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)",
        zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center",
      }}
      onClick={onDone}
    >
      <motion.div
        initial={{ scale: 0.5, y: 60 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 280, damping: 18 }}
        style={{
          background: "var(--bg-card)", borderRadius: "24px",
          padding: "3rem 3.5rem", textAlign: "center",
          border: `2px solid ${rarity.color}`,
          boxShadow: rarity.glow,
          maxWidth: "360px",
        }}
        onClick={e => e.stopPropagation()}
      >
        <motion.div
          animate={{ rotate: [0, -10, 10, -5, 5, 0] }}
          transition={{ duration: 0.6, delay: 0.2 }}
          style={{ fontSize: "3.5rem", marginBottom: "1rem" }}
        >
          {badge.badge.icon}
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <p style={{ fontSize: "0.8rem", color: rarity.color, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "0.5rem" }}>
            {rarity.label} badge unlocked!
          </p>
          <h2 style={{ fontFamily: "var(--font-heading)", fontSize: "1.5rem", fontWeight: 800, marginBottom: "0.5rem", color: rarity.color }}>
            {badge.badge.name}
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", lineHeight: 1.6, marginBottom: "1.5rem" }}>
            {badge.badge.description}
          </p>
          <Button variant="primary" onClick={onDone}>Keep going! 🚀</Button>
        </motion.div>

        {/* Particle confetti */}
        {[...Array(12)].map((_, i) => (
          <motion.div
            key={i}
            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
            animate={{
              x: (Math.random() - 0.5) * 300,
              y: (Math.random() - 0.5) * 300,
              opacity: 0,
              scale: 0,
              rotate: Math.random() * 360,
            }}
            transition={{ duration: 0.8 + Math.random() * 0.4, delay: 0.1 }}
            style={{
              position: "absolute", width: "8px", height: "8px",
              borderRadius: "2px",
              background: rarity.color,
              left: "50%", top: "50%",
              pointerEvents: "none",
            }}
          />
        ))}
      </motion.div>
    </motion.div>
  );
}

// ─── Individual badge card ──────────────────────────────────────────────────

function BadgeCard({ ub }: { ub: UserBadge }) {
  const rarity = RARITY_STYLES[ub.badge.rarity] ?? RARITY_STYLES.common;
  const locked = !ub.is_earned;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        borderRadius: "16px",
        border: `1px solid ${locked ? "var(--border-subtle)" : rarity.color + "55"}`,
        background: locked ? "var(--bg-overlay)" : `linear-gradient(135deg, var(--bg-card) 0%, ${rarity.color}08 100%)`,
        padding: "1.25rem",
        display: "flex", flexDirection: "column", alignItems: "center",
        textAlign: "center", gap: "0.5rem",
        position: "relative", overflow: "hidden",
        boxShadow: locked ? "none" : rarity.glow,
        opacity: locked ? 0.55 : 1,
        transition: "all 0.2s",
      }}
    >
      {/* Rarity shine */}
      {!locked && (ub.badge.rarity === "epic" || ub.badge.rarity === "legendary") && (
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          background: `radial-gradient(ellipse at 50% 0%, ${rarity.color}22 0%, transparent 65%)`,
        }} />
      )}

      <div style={{ fontSize: "2rem", position: "relative" }}>
        {locked ? <span style={{ filter: "grayscale(1) opacity(0.4)", fontSize: "2rem" }}>{ub.badge.icon}</span> : ub.badge.icon}
        {locked && <Lock size={14} style={{ position: "absolute", bottom: -2, right: -4, color: "#999" }} />}
      </div>

      <div>
        <p style={{ fontWeight: 700, fontSize: "0.8rem", marginBottom: "2px", color: locked ? "var(--text-secondary)" : "var(--text-primary)" }}>
          {ub.badge.name}
        </p>
        <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
          {ub.badge.description}
        </p>
      </div>

      <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", justifyContent: "center" }}>
        <BadgeChip color={ub.badge.rarity === "legendary" ? "amber" : ub.badge.rarity === "epic" ? "violet" : ub.badge.rarity === "rare" ? "cyan" : "default"} size="sm">
          {rarity.label}
        </BadgeChip>
        {ub.is_earned && <BadgeChip color="emerald" size="sm">✓ Earned</BadgeChip>}
      </div>

      {/* Progress bar for unearned badges */}
      {!ub.is_earned && ub.pct_complete > 0 && (
        <div style={{ width: "100%", height: "4px", borderRadius: "999px", background: "var(--bg-overlay)", overflow: "hidden" }}>
          <div style={{
            height: "100%", width: `${ub.pct_complete}%`,
            background: `linear-gradient(90deg, ${rarity.color}, ${rarity.color}88)`,
            borderRadius: "999px", transition: "width 0.6s ease",
          }} />
        </div>
      )}
      {!ub.is_earned && ub.pct_complete > 0 && (
        <p style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>{Math.round(ub.pct_complete)}% progress</p>
      )}
    </motion.div>
  );
}

// ─── Stats panel ────────────────────────────────────────────────────────────

function StatsPanel() {
  const { data: stats } = useQuery({ queryKey: ["badge-stats"], queryFn: () => badgeApi.getStats() });
  if (!stats) return null;

  return (
    <Card padding="lg" style={{ marginBottom: "1.75rem" }}>
      <CardHeader><CardTitle><TrendingUp size={16} style={{ marginRight: "0.5rem" }} />Achievement progress</CardTitle></CardHeader>
      <CardContent>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: "0.75rem" }}>
          {[
            { label: "Earned", value: stats.total_earned, color: "var(--accent-emerald)" },
            { label: "Available", value: stats.total_available, color: "var(--text-secondary)" },
            { label: "Common", value: stats.common_earned, color: "#9CA3AF" },
            { label: "Uncommon", value: stats.uncommon_earned, color: "#10B981" },
            { label: "Rare", value: stats.rare_earned, color: "#3B82F6" },
            { label: "Epic", value: stats.epic_earned, color: "#8B5CF6" },
            { label: "Legendary", value: stats.legendary_earned, color: "#F59E0B" },
          ].map(s => (
            <div key={s.label} style={{ textAlign: "center", padding: "0.75rem", borderRadius: "10px", background: "var(--bg-overlay)" }}>
              <p style={{ fontSize: "1.5rem", fontWeight: 800, color: s.color }}>{s.value}</p>
              <p style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>{s.label}</p>
            </div>
          ))}
        </div>

        <div style={{ marginTop: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.4rem" }}>
            <span>Overall completion</span>
            <span style={{ fontWeight: 700, color: "var(--accent-violet)" }}>{stats.completion_pct}%</span>
          </div>
          <div style={{ height: "8px", borderRadius: "999px", background: "var(--bg-overlay)", overflow: "hidden" }}>
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${stats.completion_pct}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              style={{ height: "100%", background: "var(--gradient-primary)", borderRadius: "999px" }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Main page ──────────────────────────────────────────────────────────────

export default function AchievementsPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [activeCategory, setActiveCategory] = useState("all");
  const [celebrationBadge, setCelebrationBadge] = useState<UserBadge | null>(null);

  const { data: badges, isLoading } = useQuery({
    queryKey: ["badges-all"],
    queryFn: () => badgeApi.getAll(),
  });

  const { data: pending } = useQuery({
    queryKey: ["badges-pending"],
    queryFn: () => badgeApi.getPendingCelebrations(),
    refetchInterval: 10_000,
  });

  const dismissMutation = useMutation({
    mutationFn: (badgeId: string) => badgeApi.dismissCelebration(badgeId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["badges-pending"] });
      qc.invalidateQueries({ queryKey: ["badges-all"] });
    },
  });

  // Show celebration for first pending badge
  useEffect(() => {
    if (pending?.length > 0 && !celebrationBadge) {
      setCelebrationBadge(pending[0]);
    }
  }, [pending]);

  const handleDismiss = () => {
    if (celebrationBadge) {
      dismissMutation.mutate(celebrationBadge.badge_id);
      setCelebrationBadge(null);
    }
  };

  const filtered = (badges ?? []).filter((b: UserBadge) =>
    activeCategory === "all" ||
    (activeCategory === "legendary_cat" ? b.badge.rarity === "legendary" : b.badge.category === activeCategory)
  );

  const earned = (badges ?? []).filter((b: UserBadge) => b.is_earned).length;

  return (
    <div style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.25rem" }}>Achievements</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
              {earned} badges earned · keep going to unlock more
            </p>
          </div>
          <Trophy size={32} style={{ color: "#F59E0B" }} />
        </div>

        <StatsPanel />

        {/* Category filter */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
          {CATEGORIES.map(c => (
            <button
              key={c.id}
              onClick={() => setActiveCategory(c.id)}
              style={{
                padding: "0.375rem 0.875rem", borderRadius: "999px", border: "1px solid",
                borderColor: activeCategory === c.id ? "var(--accent-violet)" : "var(--border-subtle)",
                background: activeCategory === c.id ? "var(--accent-violet)" : "transparent",
                color: activeCategory === c.id ? "#fff" : "var(--text-secondary)",
                cursor: "pointer", fontSize: "0.8rem", fontWeight: activeCategory === c.id ? 600 : 400,
                transition: "all 0.15s",
              }}
            >
              {c.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}><Spinner size="lg" /></div>
        ) : (
          <motion.div
            layout
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: "0.875rem" }}
          >
            {filtered.map((ub: UserBadge) => <BadgeCard key={ub.badge_id} ub={ub} />)}
          </motion.div>
        )}

        {/* Offer button for legendary badge */}
        <div style={{ marginTop: "2rem", textAlign: "center" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.75rem" }}>Received a job offer? Unlock the Mission Complete badge!</p>
          <Button variant="secondary" leftIcon={<Star size={15} />} onClick={() => badgeApi.markJobOffer().then(() => { qc.invalidateQueries(); addToast({ type: "success", title: "Congratulations!", message: "Legendary badge unlocked!" }); })}>
            I got a job offer! 🎉
          </Button>
        </div>
      </motion.div>

      {/* Celebration overlay */}
      <AnimatePresence>
        {celebrationBadge && (
          <CelebrationOverlay badge={celebrationBadge} onDone={handleDismiss} />
        )}
      </AnimatePresence>
    </div>
  );
}
