/**
 * RoadmapPage.tsx
 * ================
 * Career roadmap with two views:
 *  - Timeline view: vertical milestone lanes
 *  - Kanban view: Not Started / In Progress / Done columns
 *
 * Users can generate a new roadmap, update skill status,
 * and track overall progress.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Map, LayoutGrid, List, Zap, CheckCircle, Circle, Clock,
  ChevronDown, ChevronUp, RefreshCw, TrendingUp, BookOpen,
} from "lucide-react";
import { roadmapApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "../components/ui/Modal";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { RoadmapRead, RoadmapMilestoneRead, RoadmapSkillRead } from "../types/api";

// ─── Status config ─────────────────────────────────────────────────────────

const STATUS_CONFIG = {
  not_started: { label: "Not started",  color: "var(--text-secondary)", icon: <Circle size={13} /> },
  in_progress:  { label: "In progress", color: "var(--accent-amber)",   icon: <Clock size={13} /> },
  completed:    { label: "Completed",   color: "var(--accent-emerald)", icon: <CheckCircle size={13} /> },
} as const;

type SkillStatus = "not_started" | "in_progress" | "completed";

// ─── Skill chip ─────────────────────────────────────────────────────────────

function SkillChip({
  skill,
  roadmapId,
  onUpdate,
}: {
  skill: RoadmapSkillRead;
  roadmapId: string;
  onUpdate: () => void;
}) {
  const { addToast } = useUIStore();
  const status = (skill.status ?? "not_started") as SkillStatus;
  const cfg = STATUS_CONFIG[status];

  const mutation = useMutation({
    mutationFn: (s: SkillStatus) => roadmapApi.updateSkillStatus(roadmapId, skill.id, s),
    onSuccess: onUpdate,
    onError: () => addToast({ type: "error", message: "Could not update skill status." }),
  });

  const cycle = () => {
    const order: SkillStatus[] = ["not_started", "in_progress", "completed"];
    const next = order[(order.indexOf(status) + 1) % order.length];
    mutation.mutate(next);
  };

  return (
    <button
      onClick={cycle}
      title={`Click to advance: ${cfg.label}`}
      style={{
        display: "inline-flex", alignItems: "center", gap: "5px",
        padding: "4px 10px", borderRadius: "999px", border: "1px solid",
        borderColor: status === "completed" ? "rgba(16,185,129,0.4)" : status === "in_progress" ? "rgba(245,158,11,0.4)" : "var(--border-subtle)",
        background: status === "completed" ? "rgba(16,185,129,0.08)" : status === "in_progress" ? "rgba(245,158,11,0.08)" : "var(--bg-overlay)",
        color: cfg.color, cursor: "pointer", fontSize: "0.75rem",
        transition: "all 0.15s",
      }}
    >
      <span style={{ color: cfg.color }}>{cfg.icon}</span>
      {skill.skill_name}
      {skill.estimated_hours && <span style={{ color: "var(--text-secondary)", fontSize: "0.65rem" }}>{skill.estimated_hours}h</span>}
    </button>
  );
}

// ─── Timeline view ──────────────────────────────────────────────────────────

function TimelineView({ roadmap, onRefresh }: { roadmap: RoadmapRead; onRefresh: () => void }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const toggle = (id: string) => setExpanded(p => ({ ...p, [id]: !p[id] }));

  return (
    <div style={{ position: "relative", paddingLeft: "2rem" }}>
      {/* Vertical line */}
      <div style={{
        position: "absolute", left: "0.75rem", top: 0, bottom: 0,
        width: "2px", background: "var(--border-subtle)",
      }} />

      {roadmap.milestones.map((m, i) => {
        const totalSkills = m.skills.length;
        const done = m.skills.filter(s => s.status === "completed").length;
        const pct = totalSkills ? Math.round(done / totalSkills * 100) : 0;
        const isOpen = expanded[m.id] !== false; // default open

        return (
          <motion.div key={m.id} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }} style={{ marginBottom: "1.5rem", position: "relative" }}>
            {/* Timeline dot */}
            <div style={{
              position: "absolute", left: "-1.625rem", top: "0.875rem",
              width: "14px", height: "14px", borderRadius: "50%",
              background: pct === 100 ? "var(--accent-emerald)" : "var(--accent-violet)",
              border: "2px solid var(--bg-base)",
              boxShadow: pct === 100 ? "0 0 10px rgba(16,185,129,0.5)" : "0 0 10px rgba(139,92,246,0.4)",
            }} />

            <Card padding="none">
              <button
                onClick={() => toggle(m.id)}
                style={{
                  width: "100%", display: "flex", alignItems: "center", gap: "0.75rem",
                  padding: "0.875rem 1.25rem", background: "none", border: "none",
                  cursor: "pointer", borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none",
                }}
              >
                <div style={{ flex: 1, textAlign: "left" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700, fontSize: "0.9rem" }}>{m.title}</span>
                    {m.timeframe_label && <Badge color="default" size="sm">{m.timeframe_label}</Badge>}
                    {pct === 100 && <Badge color="emerald" size="sm">✓ Complete</Badge>}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "4px" }}>
                    <div style={{ height: "4px", width: "120px", borderRadius: "2px", background: "var(--bg-overlay)", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: pct === 100 ? "var(--accent-emerald)" : "var(--gradient-primary)", borderRadius: "2px", transition: "width 0.4s" }} />
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{done}/{totalSkills} skills</span>
                  </div>
                </div>
                {isOpen ? <ChevronUp size={15} style={{ color: "var(--text-secondary)" }} /> : <ChevronDown size={15} style={{ color: "var(--text-secondary)" }} />}
              </button>

              {isOpen && (
                <div style={{ padding: "1rem 1.25rem" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {m.skills.map(s => (
                      <SkillChip key={s.id} skill={s} roadmapId={roadmap.id} onUpdate={onRefresh} />
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}

// ─── Kanban view ─────────────────────────────────────────────────────────────

function KanbanView({ roadmap, onRefresh }: { roadmap: RoadmapRead; onRefresh: () => void }) {
  // Flatten skills with milestone context
  const allSkills = roadmap.milestones.flatMap(m =>
    m.skills.map(s => ({ ...s, milestone_title: m.title }))
  );

  const columns: { status: SkillStatus; label: string; color: string }[] = [
    { status: "not_started", label: "Not started", color: "var(--text-secondary)" },
    { status: "in_progress", label: "In progress", color: "var(--accent-amber)" },
    { status: "completed",   label: "Completed",   color: "var(--accent-emerald)" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem", alignItems: "start" }}>
      {columns.map(col => {
        const items = allSkills.filter(s => (s.status ?? "not_started") === col.status);
        return (
          <div key={col.status}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: col.color }} />
              <span style={{ fontWeight: 700, fontSize: "0.8rem", color: col.color }}>{col.label}</span>
              <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginLeft: "auto" }}>{items.length}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {items.map(s => (
                <motion.div key={s.id} layout initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  style={{
                    padding: "0.75rem", borderRadius: "10px",
                    background: "var(--bg-glass)", backdropFilter: "blur(12px)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  <p style={{ fontWeight: 600, fontSize: "0.8rem", marginBottom: "3px" }}>{s.skill_name}</p>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{s.milestone_title}</p>
                  {s.estimated_hours && <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginTop: "4px" }}>~{s.estimated_hours}h</p>}
                  <SkillChip skill={s} roadmapId={roadmap.id} onUpdate={onRefresh} />
                </motion.div>
              ))}
              {items.length === 0 && (
                <div style={{ textAlign: "center", padding: "1.5rem", color: "var(--text-secondary)", fontSize: "0.8rem", border: "1px dashed var(--border-subtle)", borderRadius: "10px" }}>
                  Empty
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Generate modal ──────────────────────────────────────────────────────────

function GenerateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [role, setRole] = useState("");
  const [pace, setPace] = useState<"fast" | "normal" | "thorough">("normal");

  const mutation = useMutation({
    mutationFn: () => roadmapApi.generate({ target_role: role, pace }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roadmaps"] });
      addToast({ type: "success", message: `Roadmap for "${role}" generated!` });
      onClose();
    },
    onError: () => addToast({ type: "error", message: "Generation failed." }),
  });

  return (
    <Modal open={open} onClose={onClose} title="Generate career roadmap" size="sm">
      <ModalBody>
        <Input label="Target role" value={role} onChange={e => setRole(e.target.value)} placeholder="e.g. Senior Data Engineer" fullWidth autoFocus />
        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Learning pace</p>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {(["fast", "normal", "thorough"] as const).map(p => (
              <button key={p} onClick={() => setPace(p)} style={{
                flex: 1, padding: "0.5rem", borderRadius: "8px",
                border: pace === p ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                background: pace === p ? "rgba(139,92,246,0.08)" : "transparent",
                color: pace === p ? "var(--accent-violet)" : "var(--text-secondary)",
                cursor: "pointer", fontSize: "0.8rem", fontWeight: pace === p ? 600 : 400, textTransform: "capitalize",
              }}>
                {p}
              </button>
            ))}
          </div>
        </div>
      </ModalBody>
      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={() => mutation.mutate()} loading={mutation.isPending} disabled={!role.trim()}>
          Generate roadmap
        </Button>
      </ModalFooter>
    </Modal>
  );
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function RoadmapPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [view, setView] = useState<"timeline" | "kanban">("timeline");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generateOpen, setGenerateOpen] = useState(false);

  const { data: roadmaps, isLoading } = useQuery({
    queryKey: ["roadmaps"],
    queryFn: () => roadmapApi.list(),
  });

  const { data: activeRoadmap, refetch } = useQuery({
    queryKey: ["roadmap", selectedId],
    queryFn: () => roadmapApi.get(selectedId!),
    enabled: !!selectedId,
  });

  // Default to first roadmap
  if (roadmaps?.length && !selectedId) {
    setSelectedId(roadmaps[0].id);
  }

  const allSkills = activeRoadmap?.milestones.flatMap(m => m.skills) ?? [];
  const done = allSkills.filter(s => s.status === "completed").length;
  const pct = allSkills.length ? Math.round(done / allSkills.length * 100) : 0;

  return (
    <div style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1.5rem" }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.25rem" }}>Career Roadmap</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>AI-generated learning path to your target role.</p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button variant="ghost" size="sm" onClick={() => setView("timeline")} style={{ color: view === "timeline" ? "var(--accent-violet)" : undefined }}>
              <List size={15} />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setView("kanban")} style={{ color: view === "kanban" ? "var(--accent-violet)" : undefined }}>
              <LayoutGrid size={15} />
            </Button>
            <Button variant="primary" size="sm" leftIcon={<Zap size={14} />} onClick={() => setGenerateOpen(true)}>
              New roadmap
            </Button>
          </div>
        </div>

        {isLoading && <div style={{ textAlign: "center", padding: "4rem" }}><Spinner size="lg" /></div>}

        {!isLoading && !roadmaps?.length && (
          <div style={{ textAlign: "center", padding: "5rem", color: "var(--text-secondary)" }}>
            <Map size={48} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
            <p style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No roadmap yet</p>
            <p style={{ fontSize: "0.875rem", marginBottom: "1.5rem" }}>Generate a personalised career roadmap for any role.</p>
            <Button variant="primary" leftIcon={<Zap size={15} />} onClick={() => setGenerateOpen(true)}>
              Generate your roadmap
            </Button>
          </div>
        )}

        {(roadmaps?.length ?? 0) > 0 && (
          <>
            {/* Roadmap selector */}
            {(roadmaps?.length ?? 0) > 1 && (
              <div style={{ display: "flex", gap: "0.5rem", overflowX: "auto", marginBottom: "1.25rem" }}>
                {(roadmaps ?? []).map((r: RoadmapRead) => (
                  <button
                    key={r.id}
                    onClick={() => setSelectedId(r.id)}
                    style={{
                      padding: "0.4rem 0.875rem", borderRadius: "999px", whiteSpace: "nowrap",
                      border: selectedId === r.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                      background: selectedId === r.id ? "rgba(139,92,246,0.08)" : "transparent",
                      color: selectedId === r.id ? "var(--accent-violet)" : "var(--text-secondary)",
                      cursor: "pointer", fontSize: "0.8rem", fontWeight: selectedId === r.id ? 600 : 400,
                    }}
                  >
                    {r.target_role}
                  </button>
                ))}
              </div>
            )}

            {/* Progress bar */}
            {activeRoadmap && (
              <Card padding="lg" style={{ marginBottom: "1.5rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <div>
                    <p style={{ fontWeight: 700 }}>{activeRoadmap.target_role}</p>
                    <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{activeRoadmap.pace} pace · {activeRoadmap.milestones.length} milestones</p>
                  </div>
                  <p style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--accent-violet)" }}>{pct}%</p>
                </div>
                <div style={{ height: "8px", borderRadius: "999px", background: "var(--bg-overlay)", overflow: "hidden" }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    style={{ height: "100%", background: "var(--gradient-primary)", borderRadius: "999px" }}
                  />
                </div>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.4rem" }}>{done}/{allSkills.length} skills completed</p>
              </Card>
            )}

            {/* Roadmap view */}
            {activeRoadmap && (
              <AnimatePresence mode="wait">
                {view === "timeline" ? (
                  <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <TimelineView roadmap={activeRoadmap} onRefresh={() => refetch()} />
                  </motion.div>
                ) : (
                  <motion.div key="kanban" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <KanbanView roadmap={activeRoadmap} onRefresh={() => refetch()} />
                  </motion.div>
                )}
              </AnimatePresence>
            )}
          </>
        )}
      </motion.div>

      <GenerateModal open={generateOpen} onClose={() => setGenerateOpen(false)} />
    </div>
  );
}
