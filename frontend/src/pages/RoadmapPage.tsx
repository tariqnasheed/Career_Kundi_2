/**
 * RoadmapPage.tsx
 * Personalized career roadmap — milestones, skill phases, study material,
 * practice activities, progress tracking, and skill detail views.
 */

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Map, LayoutGrid, List, Zap, CheckCircle, Circle, Clock,
  ChevronDown, ChevronUp, TrendingUp, BookOpen, Target,
  RefreshCw, Play, Lightbulb, X, Download, Search,
} from "lucide-react";
import { roadmapApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "../components/ui/Modal";
import { Spinner } from "../components/ui/Spinner";
import { SkillRadar } from "../components/features/SkillRadar";
import { useUIStore } from "../store/ui";
import type { RoadmapRead, RoadmapSkillRead } from "../types/api";

const STATUS_CONFIG = {
  not_started: { label: "Not started", color: "var(--text-secondary)", icon: <Circle size={13} /> },
  in_progress: { label: "In progress", color: "var(--accent-amber)", icon: <Clock size={13} /> },
  completed: { label: "Completed", color: "var(--accent-emerald)", icon: <CheckCircle size={13} /> },
} as const;

type SkillStatus = keyof typeof STATUS_CONFIG;

function SkillChip({ skill, roadmapId, onUpdate, onOpen }: {
  skill: RoadmapSkillRead;
  roadmapId: string;
  onUpdate: () => void;
  onOpen: () => void;
}) {
  const { addToast } = useUIStore();
  const status = (skill.status ?? "not_started") as SkillStatus;
  const cfg = STATUS_CONFIG[status];

  const mutation = useMutation({
    mutationFn: (s: SkillStatus) => roadmapApi.updateSkillStatus(roadmapId, skill.id, s),
    onSuccess: onUpdate,
    onError: () => addToast({ type: "error", message: "Could not update skill status." }),
  });

  const cycle = (e: React.MouseEvent) => {
    e.stopPropagation();
    const order: SkillStatus[] = ["not_started", "in_progress", "completed"];
    mutation.mutate(order[(order.indexOf(status) + 1) % order.length]);
  };

  return (
    <button
      onClick={onOpen}
      style={{
        display: "inline-flex", alignItems: "center", gap: "5px",
        padding: "4px 10px", borderRadius: "999px", border: "1px solid",
        borderColor: status === "completed" ? "rgba(16,185,129,0.4)" : "var(--border-subtle)",
        background: status === "completed" ? "rgba(16,185,129,0.08)" : "var(--bg-overlay)",
        color: cfg.color, cursor: "pointer", fontSize: "0.75rem",
      }}
    >
      <span onClick={cycle} style={{ display: "flex" }}>{cfg.icon}</span>
      {skill.skill_name}
      {skill.estimated_hours != null && <span style={{ opacity: 0.7, fontSize: "0.65rem" }}>{skill.estimated_hours}h</span>}
      {skill.importance && <Badge color="default" size="sm">{skill.importance}</Badge>}
    </button>
  );
}

const SAMPLE_ROLES = [
  "Software Engineer", "Senior Software Engineer", "Data Scientist", "Data Engineer",
  "Product Manager", "UX Designer", "DevOps Engineer", "Machine Learning Engineer",
  "Full Stack Developer", "Backend Developer", "Frontend Developer", "Cloud Architect",
];

function SkillDetailModal({
  skill, roadmapId, open, onClose, onRefresh,
}: {
  skill: RoadmapSkillRead | null;
  roadmapId: string;
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
}) {
  const { addToast } = useUIStore();
  const [practiceTab, setPracticeTab] = useState<"flashcards" | "quizzes" | "projects" | "reflection">("flashcards");

  const refreshMutation = useMutation({
    mutationFn: () => roadmapApi.refreshSkill(roadmapId, skill!.id),
    onSuccess: () => { onRefresh(); addToast({ type: "success", message: "Skill content refreshed." }); },
    onError: () => addToast({ type: "error", message: "Refresh failed." }),
  });

  if (!skill) return null;

  const study = skill.study_material;
  const practice = skill.practice_activities;

  return (
    <Modal open={open} onClose={onClose} title={skill.skill_name} size="lg">
      <ModalBody>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
          {skill.importance && <Badge color="violet">{skill.importance} priority</Badge>}
          {skill.estimated_hours != null && <Badge color="default">~{skill.estimated_hours}h</Badge>}
          <Badge color={skill.status === "completed" ? "emerald" : "default"}>{skill.status?.replace("_", " ")}</Badge>
        </div>

        {skill.lateral_connections?.length > 0 && (
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
            Prerequisites / related: {skill.lateral_connections.join(", ")}
          </p>
        )}

        {study && (
          <Card padding="md" style={{ marginBottom: "1rem" }}>
            <CardHeader><CardTitle style={{ fontSize: "0.9rem" }}><BookOpen size={14} style={{ display: "inline", marginRight: "6px" }} />Study Material</CardTitle></CardHeader>
            <CardContent>
              <p style={{ fontSize: "0.85rem", lineHeight: 1.6, marginBottom: "0.75rem" }}>{study.overview}</p>
              {study.key_concepts?.length > 0 && (
                <div>
                  <p style={{ fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.35rem" }}>Key concepts</p>
                  <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    {study.key_concepts.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                </div>
              )}
              {study.estimated_reading_time_minutes != null && (
                <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>~{study.estimated_reading_time_minutes} min read</p>
              )}
            </CardContent>
          </Card>
        )}

        {practice && (
          <Card padding="md" style={{ marginBottom: "1rem" }}>
            <CardHeader><CardTitle style={{ fontSize: "0.9rem" }}><Play size={14} style={{ display: "inline", marginRight: "6px" }} />Practice Session</CardTitle></CardHeader>
            <CardContent>
              <div className="skill-tabs">
                {(["flashcards", "quizzes", "projects", "reflection"] as const).map((tab) => (
                  <button key={tab} className={`skill-tab${practiceTab === tab ? " skill-tab--active" : ""}`} onClick={() => setPracticeTab(tab)}>
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>
              {practiceTab === "flashcards" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {(practice.self_assessment_questions ?? []).slice(0, 8).map((q, i) => (
                    <div key={i} className="feature-glass" style={{ padding: "0.6rem", fontSize: "0.8rem" }}>
                      <strong>Q{i + 1}:</strong> {q}
                    </div>
                  ))}
                  {!(practice.self_assessment_questions?.length) && <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Flashcards generate on skill refresh.</p>}
                </div>
              )}
              {practiceTab === "quizzes" && (
                <ol style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                  {(practice.exercises ?? []).map((ex, i) => <li key={i} style={{ marginBottom: "4px" }}>{ex}</li>)}
                </ol>
              )}
              {practiceTab === "projects" && practice.project_idea && (
                <div style={{ padding: "0.625rem", borderRadius: "8px", background: "rgba(139,92,246,0.06)" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}><Lightbulb size={12} style={{ display: "inline" }} /> Mini-project</p>
                  <p style={{ fontSize: "0.8rem" }}>{practice.project_idea}</p>
                </div>
              )}
              {practiceTab === "reflection" && (
                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                  {(practice.self_assessment_questions ?? []).map((q, i) => <li key={i}>{q}</li>)}
                </ul>
              )}
            </CardContent>
          </Card>
        )}

        {skill.resources?.length > 0 && (
          <Card padding="md">
            <CardHeader><CardTitle style={{ fontSize: "0.9rem" }}>Learning resources</CardTitle></CardHeader>
            <CardContent>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {skill.resources.map((r, i) => (
                  <a key={i} href={r.url ?? "#"} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.8rem", color: "var(--accent-violet-bright)" }}>
                    {r.title} <span style={{ color: "var(--text-secondary)" }}>({r.resource_type})</span>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </ModalBody>
      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>Close</Button>
        <Button variant="secondary" leftIcon={<RefreshCw size={14} />} onClick={() => refreshMutation.mutate()} loading={refreshMutation.isPending}>
          Refresh skill content
        </Button>
      </ModalFooter>
    </Modal>
  );
}

function TimelineView({ roadmap, onRefresh, onOpenSkill }: {
  roadmap: RoadmapRead;
  onRefresh: () => void;
  onOpenSkill: (s: RoadmapSkillRead) => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="roadmap-timeline">
      {roadmap.milestones.map((m, i) => {
        const done = m.skills.filter((s) => s.status === "completed").length;
        const pct = m.skills.length ? Math.round((done / m.skills.length) * 100) : 0;
        const isOpen = expanded[m.id] !== false;

        return (
          <motion.div key={m.id} className="roadmap-milestone" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}>
            <div className={`roadmap-milestone__dot${pct === 100 ? " roadmap-milestone__dot--done" : ""}`} />
            <Card padding="none" className="feature-glass">
              <button onClick={() => setExpanded((p) => ({ ...p, [m.id]: !isOpen }))} style={{
                width: "100%", display: "flex", alignItems: "center", gap: "0.75rem",
                padding: "0.875rem 1.25rem", background: "none", border: "none", cursor: "pointer",
                borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none",
              }}>
                <div style={{ flex: 1, textAlign: "left" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700 }}>{m.title}</span>
                    {m.timeframe_label && <Badge color="default" size="sm">{m.timeframe_label}</Badge>}
                    {pct === 100 && <Badge color="emerald" size="sm">Complete</Badge>}
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginTop: "4px" }}>
                    <div style={{ height: "4px", width: "120px", borderRadius: "2px", background: "var(--bg-overlay)", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${pct}%`, background: "var(--gradient-primary)", transition: "width 0.4s" }} />
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{done}/{m.skills.length} skills</span>
                  </div>
                </div>
                {isOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </button>
              {isOpen && (
                <div style={{ padding: "1rem 1.25rem" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                    {m.skills.map((s) => (
                      <SkillChip key={s.id} skill={s} roadmapId={roadmap.id} onUpdate={onRefresh} onOpen={() => onOpenSkill(s)} />
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

function KanbanView({ roadmap, onRefresh, onOpenSkill }: {
  roadmap: RoadmapRead;
  onRefresh: () => void;
  onOpenSkill: (s: RoadmapSkillRead) => void;
}) {
  const allSkills = roadmap.milestones.flatMap((m) => m.skills.map((s) => ({ ...s, milestone_title: m.title })));
  const columns: { status: SkillStatus; label: string; color: string }[] = [
    { status: "not_started", label: "Not started", color: "var(--text-secondary)" },
    { status: "in_progress", label: "In progress", color: "var(--accent-amber)" },
    { status: "completed", label: "Completed", color: "var(--accent-emerald)" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
      {columns.map((col) => {
        const items = allSkills.filter((s) => (s.status ?? "not_started") === col.status);
        return (
          <div key={col.status}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.75rem" }}>
              <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: col.color }} />
              <span style={{ fontWeight: 700, fontSize: "0.8rem", color: col.color }}>{col.label}</span>
              <span style={{ marginLeft: "auto", fontSize: "0.7rem", color: "var(--text-secondary)" }}>{items.length}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {items.map((s) => (
                <div key={s.id} onClick={() => onOpenSkill(s)} style={{ padding: "0.75rem", borderRadius: "10px", background: "var(--bg-glass)", border: "1px solid var(--border-subtle)", cursor: "pointer" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.8rem" }}>{s.skill_name}</p>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{s.milestone_title}</p>
                  <SkillChip skill={s} roadmapId={roadmap.id} onUpdate={onRefresh} onOpen={() => onOpenSkill(s)} />
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function GenerateModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [role, setRole] = useState("");
  const [roleQuery, setRoleQuery] = useState("");
  const [pace, setPace] = useState<"fast" | "normal" | "thorough">("normal");
  const [skillLevel, setSkillLevel] = useState<"beginner" | "intermediate" | "advanced" | "">("");
  const [weeklyHours, setWeeklyHours] = useState("");
  const [timelineMonths, setTimelineMonths] = useState("");
  const [context, setContext] = useState("");

  const mutation = useMutation({
    mutationFn: () => roadmapApi.generate({
      target_role: role,
      pace,
      starting_skill_level: skillLevel || undefined,
      personalization_inputs: {
        weekly_hours_available: weeklyHours ? Number(weeklyHours) : undefined,
        target_timeframe_months: timelineMonths ? Number(timelineMonths) : undefined,
        additional_context: context || undefined,
      },
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roadmaps"] });
      addToast({ type: "success", message: `Roadmap for "${role}" generated!` });
      onClose();
    },
    onError: () => addToast({ type: "error", message: "Generation failed." }),
  });

  const filteredRoles = SAMPLE_ROLES.filter((r) => r.toLowerCase().includes(roleQuery.toLowerCase()));

  return (
    <Modal open={open} onClose={onClose} title="Generate career roadmap" size="md">
      <ModalBody>
        <Input label="Search roles (O*NET catalogue)" value={roleQuery} onChange={(e) => setRoleQuery(e.target.value)} placeholder="Type to filter…" leftIcon={<Search size={14} />} fullWidth />
        {roleQuery && filteredRoles.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", margin: "0.5rem 0 1rem" }}>
            {filteredRoles.slice(0, 6).map((r) => (
              <button key={r} onClick={() => { setRole(r); setRoleQuery(r); }} style={{ padding: "0.3rem 0.6rem", borderRadius: "999px", border: "1px solid var(--border-subtle)", background: role === r ? "rgba(139,92,246,0.12)" : "transparent", fontSize: "0.72rem", cursor: "pointer", color: "var(--text-secondary)" }}>{r}</button>
            ))}
          </div>
        )}
        <Input label="Target role *" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. Senior Data Engineer" fullWidth />
        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Current skill level</p>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            {(["beginner", "intermediate", "advanced"] as const).map((l) => (
              <button key={l} onClick={() => setSkillLevel(l)} style={{
                flex: 1, padding: "0.45rem", borderRadius: "8px", fontSize: "0.75rem", cursor: "pointer", textTransform: "capitalize",
                border: skillLevel === l ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                background: skillLevel === l ? "rgba(139,92,246,0.08)" : "transparent",
              }}>{l}</button>
            ))}
          </div>
        </div>
        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Learning pace</p>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            {(["fast", "normal", "thorough"] as const).map((p) => (
              <button key={p} onClick={() => setPace(p)} style={{
                flex: 1, padding: "0.45rem", borderRadius: "8px", fontSize: "0.75rem", cursor: "pointer", textTransform: "capitalize",
                border: pace === p ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                background: pace === p ? "rgba(139,92,246,0.08)" : "transparent",
              }}>{p}</button>
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginTop: "1rem" }}>
          <Input label="Weekly hours available" type="number" value={weeklyHours} onChange={(e) => setWeeklyHours(e.target.value)} placeholder="10" fullWidth />
          <Input label="Target timeline (months)" type="number" value={timelineMonths} onChange={(e) => setTimelineMonths(e.target.value)} placeholder="6" fullWidth />
        </div>
        <div style={{ marginTop: "1rem" }}>
          <Textarea label="Career goals & context" value={context} onChange={(e) => setContext(e.target.value)} placeholder="e.g. I know basic SQL from a bootcamp, targeting FAANG within 12 months…" rows={3} fullWidth />
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

export default function RoadmapPage() {
  const [view, setView] = useState<"timeline" | "kanban">("timeline");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [skillDetail, setSkillDetail] = useState<RoadmapSkillRead | null>(null);

  const { data: roadmaps, isLoading } = useQuery({ queryKey: ["roadmaps"], queryFn: () => roadmapApi.list() });
  const { data: activeRoadmap, refetch } = useQuery({
    queryKey: ["roadmap", selectedId],
    queryFn: () => roadmapApi.get(selectedId!),
    enabled: !!selectedId,
  });

  useEffect(() => {
    if (roadmaps?.length && !selectedId) setSelectedId(roadmaps[0].id);
  }, [roadmaps, selectedId]);

  const allSkills = activeRoadmap?.milestones.flatMap((m) => m.skills) ?? [];
  const done = allSkills.filter((s) => s.status === "completed").length;
  const pct = allSkills.length ? Math.round((done / allSkills.length) * 100) : 0;
  const nextSkill = allSkills.find((s) => s.status === "not_started" || s.status === "in_progress");

  const radarData = allSkills.slice(0, 8).map((s) => ({
    name: s.skill_name,
    value: s.status === "completed" ? 100 : s.status === "in_progress" ? 55 : 15,
  }));

  const exportMarkdown = () => {
    if (!activeRoadmap) return;
    const lines = [`# Career Roadmap: ${activeRoadmap.target_role}`, "", `Progress: ${pct}%`, ""];
    activeRoadmap.milestones.forEach((m) => {
      lines.push(`## ${m.title}${m.timeframe_label ? ` (${m.timeframe_label})` : ""}`);
      m.skills.forEach((s) => lines.push(`- [${s.status}] ${s.skill_name}`));
      lines.push("");
    });
    const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `roadmap_${activeRoadmap.target_role.replace(/\s+/g, "_")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="feature-page">
      <div className="feature-page__inner">
      <motion.div className="feature-hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <span className="feature-hero__eyebrow"><Map size={14} /> Personalized learning path</span>
            <h1 className="feature-hero__title gradient-text">Career Roadmap</h1>
            <p className="feature-hero__subtitle">
              Interactive milestones, grounded study materials, and unlimited practice activities — adapted to your pace and skill level.
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <Button variant="ghost" size="sm" onClick={() => setView("timeline")} style={{ color: view === "timeline" ? "var(--accent-violet)" : undefined }}><List size={15} /></Button>
            <Button variant="ghost" size="sm" onClick={() => setView("kanban")} style={{ color: view === "kanban" ? "var(--accent-violet)" : undefined }}><LayoutGrid size={15} /></Button>
            {activeRoadmap && <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={exportMarkdown}>Export MD</Button>}
            <Button variant="primary" size="sm" leftIcon={<Zap size={14} />} onClick={() => setGenerateOpen(true)}>New roadmap</Button>
          </div>
        </div>
      </motion.div>

        {isLoading && <div style={{ textAlign: "center", padding: "4rem" }}><Spinner size="lg" /></div>}

        {!isLoading && !roadmaps?.length && (
          <div style={{ textAlign: "center", padding: "5rem", color: "var(--text-secondary)" }}>
            <Map size={48} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
            <p style={{ fontWeight: 600, marginBottom: "0.5rem" }}>No roadmap yet</p>
            <p style={{ fontSize: "0.875rem", marginBottom: "1.5rem" }}>Generate a personalized career transformation plan for any target role.</p>
            <Button variant="primary" leftIcon={<Zap size={15} />} onClick={() => setGenerateOpen(true)}>Generate your roadmap</Button>
          </div>
        )}

        {(roadmaps?.length ?? 0) > 0 && activeRoadmap && (
          <>
            {(roadmaps?.length ?? 0) > 1 && (
              <div style={{ display: "flex", gap: "0.5rem", overflowX: "auto", marginBottom: "1.25rem" }}>
                {roadmaps!.map((r) => (
                  <button key={r.id} onClick={() => setSelectedId(r.id)} style={{
                    padding: "0.4rem 0.875rem", borderRadius: "999px", whiteSpace: "nowrap",
                    border: selectedId === r.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                    background: selectedId === r.id ? "rgba(139,92,246,0.08)" : "transparent",
                    cursor: "pointer", fontSize: "0.8rem",
                  }}>{r.target_role}</button>
                ))}
              </div>
            )}

            <div className="feature-grid-2" style={{ marginBottom: "1.5rem" }}>
              <Card padding="lg" className="feature-glass">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div>
                  <p style={{ fontWeight: 700 }}>{activeRoadmap.target_role}</p>
                  <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                    {activeRoadmap.pace} pace · {activeRoadmap.starting_skill_level ?? "auto"} level · {activeRoadmap.milestones.length} milestones
                  </p>
                </div>
                <p style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--accent-violet)" }}>{pct}%</p>
              </div>
              <div style={{ height: "8px", borderRadius: "999px", background: "var(--bg-overlay)", overflow: "hidden" }}>
                <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} style={{ height: "100%", background: "var(--gradient-primary)", borderRadius: "999px" }} />
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.4rem" }}>{done}/{allSkills.length} skills completed</p>
              {nextSkill && (
                <div style={{ marginTop: "0.75rem", padding: "0.625rem", borderRadius: "8px", background: "rgba(139,92,246,0.06)", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                  <TrendingUp size={14} style={{ color: "var(--accent-violet)" }} />
                  <span>Next up: <strong>{nextSkill.skill_name}</strong></span>
                  <Button variant="ghost" size="sm" onClick={() => setSkillDetail(nextSkill)}>Open study view</Button>
                </div>
              )}
              </Card>
              <Card padding="lg" className="feature-glass">
                <p style={{ fontWeight: 700, marginBottom: "0.5rem", fontSize: "0.85rem" }}>Skill progress radar</p>
                <SkillRadar skills={radarData} />
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.5rem", textAlign: "center" }}>
                  GraphRAG lateral connections surface as you complete prerequisites
                </p>
              </Card>
            </div>

            <AnimatePresence mode="wait">
              {view === "timeline" ? (
                <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <TimelineView roadmap={activeRoadmap} onRefresh={() => refetch()} onOpenSkill={setSkillDetail} />
                </motion.div>
              ) : (
                <motion.div key="kanban" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <KanbanView roadmap={activeRoadmap} onRefresh={() => refetch()} onOpenSkill={setSkillDetail} />
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}

      <GenerateModal open={generateOpen} onClose={() => setGenerateOpen(false)} />
      <SkillDetailModal
        skill={skillDetail}
        roadmapId={activeRoadmap?.id ?? ""}
        open={!!skillDetail}
        onClose={() => setSkillDetail(null)}
        onRefresh={() => refetch()}
      />
      </div>
    </div>
  );
}
