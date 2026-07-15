/**
 * RoadmapPage.tsx
 * Platform-wide career roadmap — milestones, skill progress, study material.
 * ROAD-F1: UI shell. ROAD-F2: save/load. ROAD-F3: detail + skill-based tracking.
 */

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Map, LayoutGrid, List, Zap, CheckCircle, Circle, Clock,
  ChevronDown, ChevronUp, TrendingUp, BookOpen,
  RefreshCw, Play, Lightbulb, Download, Search, Trash2,
} from "lucide-react";
import { passportApi, roadmapApi, taxonomyApi } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { SkillRadar } from "@/components/features/SkillRadar";
import { useUIStore } from "@/store/ui";
import type { ApiError, RoadmapRead, RoadmapSkillRead, RoadmapTaxonomyMeta } from "@/types/api";
import {
  buildRoadmapContextFromPassportTarget,
  passportTargetsForPrefill,
  type PassportTargetPrefill,
} from "@/features/passport/passportIntegrationUtils";

function queryErrorMessage(err: unknown): string {
  const msg = (err as ApiError | undefined)?.message;
  return (msg && String(msg).trim()) || "Request failed. Please try again.";
}

const STATUS_CONFIG = {
  not_started: { label: "Not started", color: "var(--text-secondary)", icon: <Circle size={13} /> },
  in_progress: { label: "In progress", color: "var(--accent-amber)", icon: <Clock size={13} /> },
  completed: { label: "Completed", color: "var(--accent-emerald)", icon: <CheckCircle size={13} /> },
} as const;

type SkillStatus = keyof typeof STATUS_CONFIG;
const SKILL_STATUS_ORDER: SkillStatus[] = ["not_started", "in_progress", "completed"];

function skillStatusCounts(skills: RoadmapSkillRead[]) {
  return {
    not_started: skills.filter((s) => (s.status ?? "not_started") === "not_started").length,
    in_progress: skills.filter((s) => s.status === "in_progress").length,
    completed: skills.filter((s) => s.status === "completed").length,
    total: skills.length,
  };
}

function SkillStatusSelect({
  value,
  disabled,
  onChange,
}: {
  value: SkillStatus;
  disabled?: boolean;
  onChange: (next: SkillStatus) => void;
}) {
  return (
    <label className="roadmap-skill-status">
      <span className="sr-only">Skill status</span>
      <select
        value={value}
        disabled={disabled}
        aria-label="Skill status"
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => onChange(e.target.value as SkillStatus)}
      >
        {SKILL_STATUS_ORDER.map((s) => (
          <option key={s} value={s}>{STATUS_CONFIG[s].label}</option>
        ))}
      </select>
    </label>
  );
}

function SkillChip({ skill, roadmapId, onUpdate, onOpen, onActionMessage }: {
  skill: RoadmapSkillRead;
  roadmapId: string;
  onUpdate: () => void;
  onOpen: () => void;
  onActionMessage?: (msg: string, kind: "success" | "error") => void;
}) {
  const { addToast } = useUIStore();
  const status = (skill.status ?? "not_started") as SkillStatus;
  const cfg = STATUS_CONFIG[status];

  const mutation = useMutation({
    mutationFn: (s: SkillStatus) => roadmapApi.updateSkillStatus(roadmapId, skill.id, s),
    onSuccess: () => {
      onUpdate();
      addToast({ type: "success", message: "Skill status updated." });
      onActionMessage?.("Skill status updated.", "success");
    },
    onError: () => {
      addToast({ type: "error", message: "Could not update skill status. Please try again." });
      onActionMessage?.("Could not update skill status. Please try again.", "error");
    },
  });

  return (
    <div className="roadmap-skill-chip-wrap">
      <button
        type="button"
        onClick={onOpen}
        className={`roadmap-skill-chip${status === "completed" ? " is-done" : ""}`}
        style={{ color: cfg.color }}
      >
        {mutation.isPending ? <Spinner size="sm" /> : cfg.icon}
        {skill.skill_name}
        {skill.estimated_hours != null && <span className="roadmap-skill-chip__hours">{skill.estimated_hours}h</span>}
        {skill.importance && <Badge color="default" size="sm">{skill.importance}</Badge>}
      </button>
      <SkillStatusSelect
        value={status}
        disabled={mutation.isPending}
        onChange={(next) => {
          if (next !== status) mutation.mutate(next);
        }}
      />
    </div>
  );
}

function SkillTracker({
  roadmap,
  onRefresh,
  onOpenSkill,
  onActionMessage,
}: {
  roadmap: RoadmapRead;
  onRefresh: () => void;
  onOpenSkill: (s: RoadmapSkillRead) => void;
  onActionMessage: (msg: string, kind: "success" | "error") => void;
}) {
  const { addToast } = useUIStore();
  const [updatingSkillId, setUpdatingSkillId] = useState<string | null>(null);
  const [refreshingSkillId, setRefreshingSkillId] = useState<string | null>(null);

  const statusMutation = useMutation({
    mutationFn: ({ skillId, status }: { skillId: string; status: SkillStatus }) =>
      roadmapApi.updateSkillStatus(roadmap.id, skillId, status),
    onMutate: ({ skillId }) => setUpdatingSkillId(skillId),
    onSuccess: () => {
      onRefresh();
      addToast({ type: "success", message: "Skill status updated." });
      onActionMessage("Skill status updated.", "success");
    },
    onError: () => {
      addToast({ type: "error", message: "Could not update skill status. Please try again." });
      onActionMessage("Could not update skill status. Please try again.", "error");
    },
    onSettled: () => setUpdatingSkillId(null),
  });

  const refreshMutation = useMutation({
    mutationFn: (skillId: string) => roadmapApi.refreshSkill(roadmap.id, skillId),
    onMutate: (skillId) => setRefreshingSkillId(skillId),
    onSuccess: () => {
      onRefresh();
      addToast({ type: "success", message: "Skill content refreshed." });
      onActionMessage("Skill content refreshed.", "success");
    },
    onError: () => {
      addToast({ type: "error", message: "Could not refresh skill content. Please try again." });
      onActionMessage("Could not refresh skill content. Please try again.", "error");
    },
    onSettled: () => setRefreshingSkillId(null),
  });

  const rows = roadmap.milestones.flatMap((m) =>
    m.skills.map((s) => ({ skill: s, milestoneTitle: m.title }))
  );

  return (
    <section className="roadmap-skill-tracker" aria-label="Skill progress tracker">
                    <div className="roadmap-skill-tracker__head">
        <h3>Skill progress tracker</h3>
        <p>
          Milestones organize the roadmap; skills are the current actionable progress units.
          Detailed sub-task tracking comes in a later slice.
        </p>
      </div>
      {rows.length === 0 ? (
        <p className="roadmap-skill-tracker__empty">
          No skills in this roadmap yet. Try regenerating, or generate a new roadmap for your target role.
        </p>
      ) : (
      <ul className="roadmap-skill-tracker__list">
        {rows.map(({ skill, milestoneTitle }) => {
          const status = (skill.status ?? "not_started") as SkillStatus;
          const busy = updatingSkillId === skill.id || refreshingSkillId === skill.id;
          return (
            <li key={skill.id} className="roadmap-skill-card">
              <div className="roadmap-skill-card__main">
                <button type="button" className="roadmap-skill-card__title" onClick={() => onOpenSkill(skill)}>
                  <strong>{skill.skill_name}</strong>
                  <span>{milestoneTitle}</span>
                </button>
                <div className="roadmap-skill-card__meta">
                  {skill.importance && <Badge color="default" size="sm">{skill.importance}</Badge>}
                  {skill.estimated_hours != null && (
                    <span className="roadmap-skill-card__hours">~{skill.estimated_hours}h</span>
                  )}
                </div>
              </div>
              <div className="roadmap-skill-card__actions">
                <SkillStatusSelect
                  value={status}
                  disabled={busy}
                  onChange={(next) => {
                    if (next !== status) statusMutation.mutate({ skillId: skill.id, status: next });
                  }}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  leftIcon={<RefreshCw size={13} />}
                  loading={refreshingSkillId === skill.id}
                  disabled={busy}
                  onClick={() => refreshMutation.mutate(skill.id)}
                >
                  Refresh
                </Button>
                <Button variant="ghost" size="sm" onClick={() => onOpenSkill(skill)} disabled={busy}>
                  Open
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
      )}
    </section>
  );
}

const SAMPLE_ROLES = [
  "Software Engineer", "Senior Software Engineer", "Data Scientist", "Data Engineer",
  "Product Manager", "UX Designer", "DevOps Engineer", "Machine Learning Engineer",
  "Full Stack Developer", "Backend Developer", "Frontend Developer", "Cloud Architect",
];

function SkillDetailModal({
  skill, roadmapId, open, onClose, onRefresh, onActionMessage,
}: {
  skill: RoadmapSkillRead | null;
  roadmapId: string;
  open: boolean;
  onClose: () => void;
  onRefresh: () => void;
  onActionMessage?: (msg: string, kind: "success" | "error") => void;
}) {
  const { addToast } = useUIStore();
  const [practiceTab, setPracticeTab] = useState<"flashcards" | "quizzes" | "projects" | "reflection">("flashcards");

  const statusMutation = useMutation({
    mutationFn: (s: SkillStatus) => roadmapApi.updateSkillStatus(roadmapId, skill!.id, s),
    onSuccess: () => {
      onRefresh();
      addToast({ type: "success", message: "Skill status updated." });
      onActionMessage?.("Skill status updated.", "success");
    },
    onError: () => {
      addToast({ type: "error", message: "Could not update skill status. Please try again." });
      onActionMessage?.("Could not update skill status. Please try again.", "error");
    },
  });

  const refreshMutation = useMutation({
    mutationFn: () => roadmapApi.refreshSkill(roadmapId, skill!.id),
    onSuccess: () => {
      onRefresh();
      addToast({ type: "success", message: "Skill content refreshed." });
      onActionMessage?.("Skill content refreshed.", "success");
    },
    onError: (err) => {
      const raw = queryErrorMessage(err).toLowerCase();
      let message = "Skill content generation failed. Try Refresh skill content again.";
      if (raw.includes("ollama") && (raw.includes("unreachable") || raw.includes("connect") || raw.includes("refused"))) {
        message = "Local Ollama is not reachable. Start Ollama or switch LLM_PROVIDER=mock.";
      } else if (raw.includes("model") && (raw.includes("not found") || raw.includes("pull") || raw.includes("missing"))) {
        message = "Ollama model missing. Run: ollama pull llama3.1:8b";
      } else if (raw.includes("500") || raw.includes("server")) {
        message = "Server error while refreshing skill content. Please try again.";
      }
      addToast({ type: "error", message });
      onActionMessage?.(message, "error");
    },
  });

  if (!skill) return null;

  const status = (skill.status ?? "not_started") as SkillStatus;
  const study = skill.study_material;
  const practice = skill.practice_activities;
  const overview = (study?.overview || "").trim();
  const keyConcepts = study?.key_concepts?.filter((c) => (c || "").trim()) ?? [];
  const flashcards = practice?.self_assessment_questions?.filter((q) => (q || "").trim()) ?? [];
  const exercises = practice?.exercises?.filter((e) => (e || "").trim()) ?? [];
  const projectIdea = (practice?.project_idea || "").trim();
  const reflection = flashcards;

  const emptyHint = (label: string) => (
    <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
      {label}{" "}
      <button
        type="button"
        style={{ background: "none", border: "none", padding: 0, color: "var(--accent-violet-bright)", cursor: "pointer", textDecoration: "underline" }}
        onClick={() => refreshMutation.mutate()}
        disabled={refreshMutation.isPending}
      >
        Refresh skill content
      </button>
      .
    </p>
  );

  return (
    <Modal open={open} onClose={onClose} title={skill.skill_name} size="lg">
      <ModalBody>
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap", alignItems: "center" }}>
          {skill.importance && <Badge color="violet">{skill.importance} priority</Badge>}
          {skill.estimated_hours != null && <Badge color="default">~{skill.estimated_hours}h</Badge>}
          <SkillStatusSelect
            value={status}
            disabled={statusMutation.isPending || refreshMutation.isPending}
            onChange={(next) => {
              if (next !== status) statusMutation.mutate(next);
            }}
          />
          {statusMutation.isPending && <Spinner size="sm" />}
        </div>

        {skill.lateral_connections?.length > 0 && (
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
            Prerequisites / related: {skill.lateral_connections.join(", ")}
          </p>
        )}

        <Card padding="md" style={{ marginBottom: "1rem" }}>
          <CardHeader><CardTitle style={{ fontSize: "0.9rem" }}><BookOpen size={14} style={{ display: "inline", marginRight: "6px" }} />Study Material</CardTitle></CardHeader>
          <CardContent>
            {overview ? (
              <p style={{ fontSize: "0.85rem", lineHeight: 1.6, marginBottom: "0.75rem" }}>{overview}</p>
            ) : (
              emptyHint("No study material generated yet.")
            )}
            {keyConcepts.length > 0 && (
              <div>
                <p style={{ fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.35rem" }}>Key concepts</p>
                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  {keyConcepts.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}
            {study?.estimated_reading_time_minutes != null && overview && (
              <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>~{study.estimated_reading_time_minutes} min read</p>
            )}
          </CardContent>
        </Card>

        <Card padding="md" style={{ marginBottom: "1rem" }}>
          <CardHeader><CardTitle style={{ fontSize: "0.9rem" }}><Play size={14} style={{ display: "inline", marginRight: "6px" }} />Practice Session</CardTitle></CardHeader>
          <CardContent>
            <div className="skill-tabs">
              {(["flashcards", "quizzes", "projects", "reflection"] as const).map((tab) => (
                <button key={tab} type="button" className={`skill-tab${practiceTab === tab ? " skill-tab--active" : ""}`} onClick={() => setPracticeTab(tab)}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
            {practiceTab === "flashcards" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {flashcards.slice(0, 8).map((q, i) => (
                  <div key={i} className="feature-glass" style={{ padding: "0.6rem", fontSize: "0.8rem" }}>
                    <strong>Q{i + 1}:</strong> {q}
                  </div>
                ))}
                {!flashcards.length && emptyHint("No flashcards yet.")}
              </div>
            )}
            {practiceTab === "quizzes" && (
              exercises.length > 0 ? (
                <ol style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                  {exercises.map((ex, i) => <li key={i} style={{ marginBottom: "4px" }}>{ex}</li>)}
                </ol>
              ) : emptyHint("No quizzes yet.")
            )}
            {practiceTab === "projects" && (
              projectIdea ? (
                <div style={{ padding: "0.625rem", borderRadius: "8px", background: "rgba(139,92,246,0.06)" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 600, marginBottom: "0.25rem" }}><Lightbulb size={12} style={{ display: "inline" }} /> Mini-project</p>
                  <p style={{ fontSize: "0.8rem" }}>{projectIdea}</p>
                </div>
              ) : emptyHint("No mini-project yet.")
            )}
            {practiceTab === "reflection" && (
              reflection.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.8rem" }}>
                  {reflection.map((q, i) => <li key={i}>{q}</li>)}
                </ul>
              ) : emptyHint("No reflection questions yet.")
            )}
          </CardContent>
        </Card>

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

function TimelineView({ roadmap, onRefresh, onOpenSkill, onActionMessage }: {
  roadmap: RoadmapRead;
  onRefresh: () => void;
  onOpenSkill: (s: RoadmapSkillRead) => void;
  onActionMessage?: (msg: string, kind: "success" | "error") => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div className="roadmap-timeline roadmap-milestone-list">
      {roadmap.milestones.map((m, i) => {
        const done = m.skills.filter((s) => s.status === "completed").length;
        const pct = m.skills.length ? Math.round((done / m.skills.length) * 100) : 0;
        const isOpen = expanded[m.id] !== false;

        return (
          <motion.div key={m.id} className="roadmap-milestone" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}>
            <div className={`roadmap-milestone__dot${pct === 100 ? " roadmap-milestone__dot--done" : ""}`} />
            <Card padding="none" className="feature-glass">
              <button type="button" onClick={() => setExpanded((p) => ({ ...p, [m.id]: !isOpen }))} style={{
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
                      <SkillChip
                        key={s.id}
                        skill={s}
                        roadmapId={roadmap.id}
                        onUpdate={onRefresh}
                        onOpen={() => onOpenSkill(s)}
                        onActionMessage={onActionMessage}
                      />
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

function KanbanView({ roadmap, onRefresh, onOpenSkill, onActionMessage }: {
  roadmap: RoadmapRead;
  onRefresh: () => void;
  onOpenSkill: (s: RoadmapSkillRead) => void;
  onActionMessage?: (msg: string, kind: "success" | "error") => void;
}) {
  const allSkills = roadmap.milestones.flatMap((m) => m.skills.map((s) => ({ ...s, milestone_title: m.title })));
  const columns: { status: SkillStatus; label: string; color: string }[] = [
    { status: "not_started", label: "Not started", color: "var(--text-secondary)" },
    { status: "in_progress", label: "In progress", color: "var(--accent-amber)" },
    { status: "completed", label: "Completed", color: "var(--accent-emerald)" },
  ];

  return (
    <div className="roadmap-kanban-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1rem" }}>
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
                <div key={s.id} className="roadmap-skill-card" style={{ padding: "0.75rem" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.8rem" }}>{s.skill_name}</p>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginBottom: "0.4rem" }}>{s.milestone_title}</p>
                  <SkillChip
                    skill={s}
                    roadmapId={roadmap.id}
                    onUpdate={onRefresh}
                    onOpen={() => onOpenSkill(s)}
                    onActionMessage={onActionMessage}
                  />
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

type RoleIntelPhase =
  | "empty"
  | "ready"
  | "loading"
  | "suggested"
  | "unknown"
  | "accepted"
  | "kept_freeform"
  | "unavailable";

function extractRoadmapTaxonomy(inputs: RoadmapRead["personalization_inputs"] | undefined): RoadmapTaxonomyMeta | null {
  const raw = inputs && typeof inputs === "object" ? (inputs as { _taxonomy?: unknown })._taxonomy : null;
  if (!raw || typeof raw !== "object") return null;
  return raw as RoadmapTaxonomyMeta;
}

function phaseFromTaxonomyMeta(meta: RoadmapTaxonomyMeta | null, roleText: string): RoleIntelPhase {
  if (!roleText.trim()) return "empty";
  if (!meta) return "ready";
  if (meta.accepted_by_user) return "accepted";
  if (meta.kept_freeform) return "kept_freeform";
  if (meta.matched_role_id) return "suggested";
  return "unknown";
}

function formatTaxonomyLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return String(value).replace(/_/g, " ");
}

function RoleIntelligenceCard({
  phase,
  roleText,
  meta,
  onCheck,
  onAccept,
  onKeepFreeform,
  onRecheck,
  compact = false,
}: {
  phase: RoleIntelPhase;
  roleText: string;
  meta: RoadmapTaxonomyMeta | null;
  onCheck?: () => void;
  onAccept?: () => void;
  onKeepFreeform?: () => void;
  onRecheck?: () => void;
  compact?: boolean;
}) {
  const canCheck = phase !== "loading" && roleText.trim().length > 0 && Boolean(onCheck);
  const title = meta?.matched_role_title || meta?.matched_role_id || null;
  const skillLabels = meta?.suggested_skill_labels?.length
    ? meta.suggested_skill_labels
    : (meta?.suggested_skill_ids || []).map(formatTaxonomyLabel);

  return (
    <section
      className={`roadmap-role-intelligence${compact ? " roadmap-role-intelligence--compact" : ""}`}
      aria-label="Role Intelligence"
      aria-live="polite"
    >
      <div className="roadmap-role-intelligence__header">
        <div>
          <p className="roadmap-role-intelligence__eyebrow">Role intelligence</p>
          <h3>Canonical role hint</h3>
        </div>
        {phase !== "empty" && phase !== "ready" && (
          <span
            className={`roadmap-role-intelligence__chip roadmap-role-intelligence__chip--${
              phase === "accepted"
                ? "accepted"
                : phase === "unknown" || phase === "unavailable"
                  ? "unknown"
                  : phase === "kept_freeform"
                    ? "freeform"
                    : "suggested"
            }`}
          >
            {phase === "loading"
              ? "Checking"
              : phase === "accepted"
                ? "Using suggested"
                : phase === "kept_freeform"
                  ? "Using your wording"
                  : phase === "unknown"
                    ? "No match"
                    : phase === "unavailable"
                      ? "Unavailable"
                      : "Suggested"}
          </span>
        )}
      </div>
      <p className="roadmap-role-intelligence__advisory">
        Role intelligence is advisory. It never blocks roadmap generation.
      </p>

      {phase === "empty" && (
        <p className="roadmap-role-intelligence__body">
          Add a target role to check role intelligence.
        </p>
      )}
      {phase === "ready" && (
        <p className="roadmap-role-intelligence__body">
          Check for a deterministic suggested role match when you are ready.
        </p>
      )}
      {phase === "loading" && (
        <p className="roadmap-role-intelligence__body">Checking role match…</p>
      )}
      {phase === "suggested" && (
        <div className="roadmap-role-intelligence__result">
          <p className="roadmap-role-intelligence__result-label">Suggested role match</p>
          <p className="roadmap-role-intelligence__canonical">{title || "Suggested role"}</p>
          <p className="roadmap-role-intelligence__original">
            Your wording: <strong>{roleText}</strong>
          </p>
          <div className="roadmap-role-intelligence__meta">
            <span>Source: {formatTaxonomyLabel(meta?.source)}</span>
            <span>Confidence: {formatTaxonomyLabel(meta?.confidence)}</span>
          </div>
          {meta?.explanation && (
            <p className="roadmap-role-intelligence__explain">{meta.explanation}</p>
          )}
          {skillLabels.length > 0 && (
            <div className="roadmap-role-intelligence__skills">
              <p className="roadmap-role-intelligence__result-label">Suggested skills from role intelligence</p>
              <ul>
                {skillLabels.slice(0, 6).map((label) => (
                  <li key={label}>{label}</li>
                ))}
              </ul>
              <p className="roadmap-role-intelligence__skills-note">
                Suggested skills are advisory only. They do not replace roadmap tracker skills.
              </p>
            </div>
          )}
        </div>
      )}
      {phase === "unknown" && (
        <div className="roadmap-role-intelligence__result">
          <p className="roadmap-role-intelligence__result-label">No deterministic role match found</p>
          <p className="roadmap-role-intelligence__body">
            You can still continue with your own roadmap target.
          </p>
        </div>
      )}
      {phase === "accepted" && (
        <div className="roadmap-role-intelligence__result">
          <p className="roadmap-role-intelligence__result-label">Using suggested role</p>
          <p className="roadmap-role-intelligence__canonical">{title}</p>
          <div className="roadmap-role-intelligence__meta">
            <span>Source: {formatTaxonomyLabel(meta?.source)}</span>
            <span>Confidence: {formatTaxonomyLabel(meta?.confidence)}</span>
          </div>
          {skillLabels.length > 0 && (
            <div className="roadmap-role-intelligence__skills">
              <p className="roadmap-role-intelligence__result-label">Suggested skills from role intelligence</p>
              <ul>
                {skillLabels.slice(0, 6).map((label) => (
                  <li key={label}>{label}</li>
                ))}
              </ul>
              <p className="roadmap-role-intelligence__skills-note">
                Suggested skills are advisory only.
              </p>
            </div>
          )}
        </div>
      )}
      {phase === "kept_freeform" && (
        <div className="roadmap-role-intelligence__result">
          <p className="roadmap-role-intelligence__result-label">Using your wording</p>
          <p className="roadmap-role-intelligence__original">
            <strong>{roleText || meta?.target_role_text}</strong>
          </p>
        </div>
      )}
      {phase === "unavailable" && (
        <p className="roadmap-role-intelligence__body">
          Role intelligence is unavailable right now. You can continue without it.
        </p>
      )}

      {(onCheck || onAccept || onKeepFreeform || onRecheck) && (
        <div className="roadmap-role-intelligence__actions">
          {phase === "loading" && (
            <Button variant="secondary" size="sm" loading disabled>
              Checking role match…
            </Button>
          )}
          {(phase === "empty" ||
            phase === "ready" ||
            phase === "suggested" ||
            phase === "unknown" ||
            phase === "unavailable") &&
            onCheck && (
              <Button variant="secondary" size="sm" disabled={!canCheck} onClick={onCheck}>
                Check role match
              </Button>
            )}
          {phase === "suggested" && onAccept && (
            <Button variant="primary" size="sm" onClick={onAccept}>
              Use suggested role
            </Button>
          )}
          {(phase === "suggested" || phase === "unknown") && onKeepFreeform && (
            <Button variant="ghost" size="sm" onClick={onKeepFreeform}>
              Keep my wording
            </Button>
          )}
          {(phase === "accepted" || phase === "kept_freeform") && onRecheck && (
            <Button variant="ghost" size="sm" onClick={onRecheck}>
              Re-check
            </Button>
          )}
        </div>
      )}
    </section>
  );
}

function GenerateModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (roadmap: RoadmapRead) => void;
}) {
  const { addToast } = useUIStore();
  const [role, setRole] = useState("");
  const [roleQuery, setRoleQuery] = useState("");
  const [pace, setPace] = useState<"fast" | "normal" | "thorough">("normal");
  const [skillLevel, setSkillLevel] = useState<"beginner" | "intermediate" | "advanced" | "">("");
  const [weeklyHours, setWeeklyHours] = useState("");
  const [timelineMonths, setTimelineMonths] = useState("");
  const [context, setContext] = useState("");
  const [roleIntelPhase, setRoleIntelPhase] = useState<RoleIntelPhase>("empty");
  const [taxonomyMeta, setTaxonomyMeta] = useState<RoadmapTaxonomyMeta | null>(null);
  const [selectedPassportTarget, setSelectedPassportTarget] =
    useState<PassportTargetPrefill | null>(null);

  const passportQuery = useQuery({
    queryKey: ["passport", "aggregate"],
    queryFn: () => passportApi.get(),
    enabled: open,
    retry: false,
  });
  const passportTargets = passportTargetsForPrefill(passportQuery.data);

  useEffect(() => {
    if (!open) return;
    setRole("");
    setRoleQuery("");
    setPace("normal");
    setSkillLevel("");
    setWeeklyHours("");
    setTimelineMonths("");
    setContext("");
    setRoleIntelPhase("empty");
    setTaxonomyMeta(null);
    setSelectedPassportTarget(null);
  }, [open]);

  const applyPassportTarget = (target: PassportTargetPrefill) => {
    setSelectedPassportTarget(target);
    setRole(target.target_role_text);
    setTaxonomyMeta(null);
    setRoleIntelPhase(target.target_role_text.trim() ? "ready" : "empty");
    const prefix = buildRoadmapContextFromPassportTarget(target);
    setContext((prev) => {
      if (!prev.trim()) return prefix;
      if (prev.includes("Passport career target:")) return prev;
      return `${prefix}\n\n${prev}`;
    });
  };

  const handleRoleChange = (value: string) => {
    setRole(value);
    setTaxonomyMeta(null);
    setRoleIntelPhase(value.trim() ? "ready" : "empty");
  };

  const checkRoleMatch = async () => {
    const text = role.trim();
    if (!text) {
      setRoleIntelPhase("empty");
      return;
    }
    setRoleIntelPhase("loading");
    try {
      const match = await taxonomyApi.matchRole({
        input_text: text,
        source: "user_provided",
        confidence: "suggested",
      });
      let title: string | null = null;
      let skillIds: string[] = [];
      let skillLabels: string[] = [];
      if (match.matched_role_id) {
        try {
          const roleDetail = await taxonomyApi.getRole(match.matched_role_id);
          title = roleDetail.title;
        } catch {
          title = match.matched_role_id;
        }
        try {
          const skills = await taxonomyApi.getRoleSkills(match.matched_role_id);
          skillIds = skills.skills.map((s) => s.id);
          skillLabels = skills.skills.map((s) => s.label);
        } catch {
          skillIds = [];
          skillLabels = [];
        }
      }
      const meta: RoadmapTaxonomyMeta = {
        target_role_text: text,
        matched_role_id: match.matched_role_id,
        matched_skill_id: match.matched_skill_id,
        normalized_text: match.normalized_text,
        source: match.source,
        confidence: match.confidence,
        explanation: match.explanation,
        accepted_by_user: false,
        kept_freeform: false,
        matched_role_title: title,
        suggested_skill_ids: skillIds,
        suggested_skill_labels: skillLabels,
      };
      setTaxonomyMeta(meta);
      setRoleIntelPhase(match.matched_role_id ? "suggested" : "unknown");
    } catch {
      setTaxonomyMeta(null);
      setRoleIntelPhase("unavailable");
    }
  };

  const acceptSuggestedRole = () => {
    if (!taxonomyMeta?.matched_role_id) return;
    const canonical =
      taxonomyMeta.matched_role_title || taxonomyMeta.matched_role_id;
    setRole(canonical);
    setTaxonomyMeta({
      ...taxonomyMeta,
      target_role_text: canonical,
      accepted_by_user: true,
      kept_freeform: false,
      matched_role_title: canonical,
    });
    setRoleIntelPhase("accepted");
  };

  const keepFreeform = () => {
    const text = role.trim();
    setTaxonomyMeta({
      ...(taxonomyMeta || {}),
      target_role_text: text,
      accepted_by_user: false,
      kept_freeform: true,
      matched_role_id: taxonomyMeta?.matched_role_id ?? null,
      matched_skill_id: taxonomyMeta?.matched_skill_id ?? null,
      normalized_text: taxonomyMeta?.normalized_text ?? null,
      source: taxonomyMeta?.source ?? "user_provided",
      confidence: taxonomyMeta?.confidence ?? "unknown",
      explanation: taxonomyMeta?.explanation ?? "Keeping freeform role wording.",
      matched_role_title: taxonomyMeta?.matched_role_title ?? null,
      suggested_skill_ids: taxonomyMeta?.suggested_skill_ids ?? [],
      suggested_skill_labels: taxonomyMeta?.suggested_skill_labels ?? [],
    });
    setRoleIntelPhase("kept_freeform");
  };

  const mutation = useMutation({
    mutationFn: () => {
      const personalization_inputs: Record<string, unknown> = {
        weekly_hours_available: weeklyHours ? Number(weeklyHours) : undefined,
        target_timeframe_months: timelineMonths ? Number(timelineMonths) : undefined,
        additional_context: context || undefined,
      };
      if (selectedPassportTarget) {
        personalization_inputs.passport_target_prefill = {
          target_role_text: selectedPassportTarget.target_role_text,
          target_country: selectedPassportTarget.target_country,
          target_region: selectedPassportTarget.target_region,
          target_seniority: selectedPassportTarget.target_seniority,
          time_horizon: selectedPassportTarget.time_horizon,
          priority: selectedPassportTarget.priority,
        };
      }
      if (taxonomyMeta) {
        personalization_inputs._taxonomy = {
          ...taxonomyMeta,
          target_role_text: role.trim() || taxonomyMeta.target_role_text || null,
        };
      }
      return roadmapApi.generate({
        target_role: role.trim(),
        pace,
        starting_skill_level: skillLevel || undefined,
        personalization_inputs,
      });
    },
    onSuccess: (created) => {
      addToast({ type: "success", message: "Roadmap created." });
      onCreated(created);
      onClose();
    },
    onError: () => addToast({ type: "error", message: "Could not create roadmap. Please try again." }),
  });

  const filteredRoles = SAMPLE_ROLES.filter((r) => r.toLowerCase().includes(roleQuery.toLowerCase()));

  return (
    <Modal open={open} onClose={onClose} title="Generate career roadmap" size="md">
      <ModalBody>
        <Input label="Search roles (O*NET catalogue)" value={roleQuery} onChange={(e) => setRoleQuery(e.target.value)} placeholder="Type to filter…" leftIcon={<Search size={14} />} fullWidth />
        {roleQuery && filteredRoles.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", margin: "0.5rem 0 1rem" }}>
            {filteredRoles.slice(0, 6).map((r) => (
              <button key={r} type="button" onClick={() => { handleRoleChange(r); setRoleQuery(r); }} style={{ padding: "0.3rem 0.6rem", borderRadius: "999px", border: "1px solid var(--border-subtle)", background: role === r ? "rgba(139,92,246,0.12)" : "transparent", fontSize: "0.72rem", cursor: "pointer", color: "var(--text-secondary)" }}>{r}</button>
            ))}
          </div>
        )}
        <Input label="Target role *" value={role} onChange={(e) => handleRoleChange(e.target.value)} placeholder="e.g. Senior Data Engineer" fullWidth />

        {(passportQuery.isSuccess && passportTargets.length > 0) && (
          <div
            data-testid="roadmap-passport-prefill"
            style={{
              marginTop: "0.85rem",
              padding: "0.75rem",
              borderRadius: "10px",
              border: "1px solid var(--border-subtle)",
              background: "var(--bg-overlay)",
            }}
          >
            <p style={{ margin: "0 0 0.4rem", fontSize: "0.8rem", fontWeight: 600 }}>
              Use a Career Passport target
            </p>
            <p style={{ margin: "0 0 0.55rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              This creates a new Roadmap. It does not change your Passport target.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
              {passportTargets.slice(0, 5).map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => applyPassportTarget(t)}
                  style={{
                    padding: "0.3rem 0.6rem",
                    borderRadius: "999px",
                    border:
                      selectedPassportTarget?.id === t.id
                        ? "2px solid var(--accent-violet)"
                        : "1px solid var(--border-subtle)",
                    background:
                      selectedPassportTarget?.id === t.id
                        ? "rgba(139,92,246,0.12)"
                        : "transparent",
                    fontSize: "0.72rem",
                    cursor: "pointer",
                    color: "var(--text-secondary)",
                  }}
                >
                  {t.target_role_text}
                </button>
              ))}
            </div>
          </div>
        )}
        {passportQuery.isError && (
          <p role="status" style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Passport targets could not be loaded. You can still generate a Roadmap manually.
          </p>
        )}

        <RoleIntelligenceCard
          phase={roleIntelPhase}
          roleText={role}
          meta={taxonomyMeta}
          onCheck={() => void checkRoleMatch()}
          onAccept={acceptSuggestedRole}
          onKeepFreeform={keepFreeform}
          onRecheck={() => {
            setTaxonomyMeta(null);
            setRoleIntelPhase(role.trim() ? "ready" : "empty");
          }}
        />

        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Current skill level</p>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            {(["beginner", "intermediate", "advanced"] as const).map((l) => (
              <button key={l} type="button" onClick={() => setSkillLevel(l)} style={{
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
              <button key={p} type="button" onClick={() => setPace(p)} style={{
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
        <Button variant="ghost" onClick={onClose} disabled={mutation.isPending}>Cancel</Button>
        <Button variant="primary" onClick={() => mutation.mutate()} loading={mutation.isPending} disabled={!role.trim() || mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Generate roadmap"}
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export default function RoadmapPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [view, setView] = useState<"timeline" | "kanban">("timeline");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [skillDetail, setSkillDetail] = useState<RoadmapSkillRead | null>(null);
  const [roadmapSuccess, setRoadmapSuccess] = useState<string | null>(null);
  const [roadmapActionError, setRoadmapActionError] = useState<string | null>(null);

  const handleActionMessage = (msg: string, kind: "success" | "error") => {
    if (kind === "success") {
      setRoadmapSuccess(msg);
      setRoadmapActionError(null);
    } else {
      setRoadmapActionError(msg);
      setRoadmapSuccess(null);
    }
  };

  const {
    data: roadmaps,
    isLoading,
    isError,
    error,
    refetch: refetchList,
  } = useQuery({ queryKey: ["roadmaps"], queryFn: () => roadmapApi.list() });

  const {
    data: activeRoadmap,
    isLoading: detailLoading,
    isError: detailError,
    refetch,
  } = useQuery({
    queryKey: ["roadmap", selectedId],
    queryFn: () => roadmapApi.get(selectedId!),
    enabled: !!selectedId,
  });

  useEffect(() => {
    if (roadmaps?.length && !selectedId) setSelectedId(roadmaps[0].id);
  }, [roadmaps, selectedId]);

  useEffect(() => {
    if (!skillDetail || !activeRoadmap) return;
    const fresh = activeRoadmap.milestones
      .flatMap((m) => m.skills)
      .find((s) => s.id === skillDetail.id);
    if (!fresh) return;
    if (
      fresh.status !== skillDetail.status ||
      fresh.resources?.length !== skillDetail.resources?.length ||
      fresh.study_material?.overview !== skillDetail.study_material?.overview
    ) {
      setSkillDetail(fresh);
    }
  }, [activeRoadmap, skillDetail]);

  const deleteMutation = useMutation({
    mutationFn: (id: string) => roadmapApi.delete(id),
    onSuccess: async (_void, id) => {
      // Cancel/remove detail query first so we never refetch a deleted id (ROAD-F4).
      await qc.cancelQueries({ queryKey: ["roadmap", id] });
      qc.removeQueries({ queryKey: ["roadmap", id] });
      setSelectedId((curr) => (curr === id ? null : curr));
      qc.setQueryData<RoadmapRead[] | undefined>(["roadmaps"], (old) =>
        Array.isArray(old) ? old.filter((r) => r.id !== id) : old
      );
      await qc.invalidateQueries({ queryKey: ["roadmaps"] });
      setRoadmapSuccess("Roadmap deleted.");
      addToast({ type: "success", message: "Roadmap deleted." });
    },
    onError: () => addToast({ type: "error", message: "Could not delete roadmap. Please try again." }),
  });

  const regenerateMutation = useMutation({
    mutationFn: () => {
      if (!activeRoadmap) throw new Error("No roadmap selected");
      return roadmapApi.regenerate(activeRoadmap.id, {
        target_role: activeRoadmap.target_role,
        pace: activeRoadmap.pace,
        starting_skill_level: activeRoadmap.starting_skill_level ?? undefined,
        personalization_inputs: activeRoadmap.personalization_inputs,
      });
    },
    onSuccess: async (updated) => {
      await qc.invalidateQueries({ queryKey: ["roadmaps"] });
      await qc.invalidateQueries({ queryKey: ["roadmap", updated.id] });
      setSelectedId(updated.id);
      setRoadmapSuccess("Roadmap regenerated.");
      addToast({ type: "success", message: "Roadmap regenerated." });
    },
    onError: () => addToast({ type: "error", message: "Could not regenerate roadmap. Please try again." }),
  });

  const handleCreated = async (created: RoadmapRead) => {
    await qc.invalidateQueries({ queryKey: ["roadmaps"] });
    qc.setQueryData(["roadmap", created.id], created);
    setSelectedId(created.id);
    setRoadmapSuccess("Roadmap created.");
  };

  const confirmDelete = () => {
    if (!activeRoadmap) return;
    const ok = window.confirm(
      `Delete roadmap for "${activeRoadmap.target_role}"? This cannot be undone.`
    );
    if (ok) deleteMutation.mutate(activeRoadmap.id);
  };

  const confirmRegenerate = () => {
    if (!activeRoadmap) return;
    const ok = window.confirm(
      `Regenerate roadmap for "${activeRoadmap.target_role}"? Existing milestones and skills will be replaced.`
    );
    if (ok) regenerateMutation.mutate();
  };

  const allSkills = (activeRoadmap?.milestones ?? []).flatMap((m) => m.skills ?? []);
  const counts = skillStatusCounts(allSkills);
  const done = counts.completed;
  const pct = counts.total ? Math.round((done / counts.total) * 100) : 0;
  const nextSkill = allSkills.find((s) => s.status === "not_started" || s.status === "in_progress");

  const radarData = allSkills.slice(0, 8).map((s) => ({
    name: s.skill_name,
    value: s.status === "completed" ? 100 : s.status === "in_progress" ? 55 : 15,
  }));

  const listErrorMessage =
    (error as { message?: string } | undefined)?.message ||
    "Could not load your roadmaps. Please try again.";

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

  const pathwayExamples = [
    "Skill gap plan",
    "Career switch plan",
    "Graduate launch plan",
    "Study / exam path",
    "Interview preparation path",
    "Job application path",
  ];

  const isBusy = deleteMutation.isPending || regenerateMutation.isPending;

  return (
    <div className="feature-page roadmap-page">
      <div className="feature-page__inner">
        <motion.div className="feature-hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <span className="feature-hero__eyebrow"><Map size={14} /> Platform-wide career planning</span>
              <h1 className="feature-hero__title gradient-text">Career Roadmap</h1>
              <p className="feature-hero__subtitle">
                Build a structured pathway for any career goal — skill gaps, career switches, graduate launch,
                study plans, interview prep, and job-search paths. Progress is tracked from saved milestones and skills.
              </p>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <Button variant="ghost" size="sm" onClick={() => setView("timeline")} style={{ color: view === "timeline" ? "var(--accent-violet)" : undefined }} aria-pressed={view === "timeline"}><List size={15} /> Timeline</Button>
              <Button variant="ghost" size="sm" onClick={() => setView("kanban")} style={{ color: view === "kanban" ? "var(--accent-violet)" : undefined }} aria-pressed={view === "kanban"}><LayoutGrid size={15} /> Board</Button>
              {activeRoadmap && <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={exportMarkdown}>Export MD</Button>}
              {activeRoadmap && (
                <Button
                  variant="secondary"
                  size="sm"
                  leftIcon={<RefreshCw size={14} />}
                  onClick={confirmRegenerate}
                  loading={regenerateMutation.isPending}
                  disabled={isBusy}
                >
                  Regenerate
                </Button>
              )}
              {activeRoadmap && (
                <Button
                  variant="ghost"
                  size="sm"
                  leftIcon={<Trash2 size={14} />}
                  onClick={confirmDelete}
                  loading={deleteMutation.isPending}
                  disabled={isBusy}
                >
                  Delete
                </Button>
              )}
              <Button variant="primary" size="sm" leftIcon={<Zap size={14} />} onClick={() => setGenerateOpen(true)} disabled={isBusy}>
                New roadmap
              </Button>
            </div>
          </div>
        </motion.div>

        <div className="roadmap-status-strip" aria-live="polite">
          {isLoading && (
            <div className="roadmap-status-strip__row roadmap-status-strip__row--loading">
              <Spinner size="sm" />
              <span>Loading your roadmaps from the server…</span>
            </div>
          )}
          {isError && (
            <div className="roadmap-status-strip__row roadmap-status-strip__row--error roadmap-error" role="alert">
              <span>{listErrorMessage}</span>
              <Button variant="ghost" size="sm" onClick={() => void refetchList()}>Retry</Button>
            </div>
          )}
          {!isLoading && !isError && !(roadmaps?.length) && (
            <div className="roadmap-status-strip__row">
              No saved roadmaps yet. Generate one to start planning.
            </div>
          )}
          {!isLoading && !isError && !!roadmaps?.length && (
            <div className="roadmap-status-strip__row roadmap-status-strip__row--ok">
              Loaded {roadmaps.length} roadmap{roadmaps.length === 1 ? "" : "s"} from your account.
              {selectedId ? " Viewing selected pathway below." : ""}
            </div>
          )}
          {roadmapSuccess && (
            <div className="roadmap-status-strip__row roadmap-success roadmap-action-status">
              <span>{roadmapSuccess}</span>
              <Button variant="ghost" size="sm" onClick={() => setRoadmapSuccess(null)}>Dismiss</Button>
            </div>
          )}
          {roadmapActionError && (
            <div className="roadmap-status-strip__row roadmap-status-strip__row--error roadmap-error roadmap-action-status" role="alert">
              <span>{roadmapActionError}</span>
              <Button variant="ghost" size="sm" onClick={() => setRoadmapActionError(null)}>Dismiss</Button>
            </div>
          )}
          {(deleteMutation.isPending || regenerateMutation.isPending) && (
            <div className="roadmap-status-strip__row roadmap-status-strip__row--loading">
              <Spinner size="sm" />
              <span>{regenerateMutation.isPending ? "Regenerating roadmap…" : "Deleting roadmap…"}</span>
            </div>
          )}
        </div>

        <div className="roadmap-layout">
          <div className="roadmap-layout__main">
            {isLoading && (
              <div style={{ textAlign: "center", padding: "4rem" }}><Spinner size="lg" /></div>
            )}

            {!isLoading && !isError && !roadmaps?.length && (
              <div className="roadmap-empty">
                <Map size={48} className="roadmap-empty__icon" aria-hidden />
                <h2>No roadmap yet</h2>
                <p>
                  Generate a personalized career pathway for any target role. Roadmaps are platform-wide —
                  not limited to graduate launch.
                </p>
                <ul className="roadmap-empty__examples">
                  {pathwayExamples.map((ex) => (
                    <li key={ex}>{ex}</li>
                  ))}
                </ul>
                <Button variant="primary" leftIcon={<Zap size={15} />} onClick={() => setGenerateOpen(true)}>
                  Generate your roadmap
                </Button>
              </div>
            )}

            {!isLoading && !isError && !!roadmaps?.length && (
              <>
                <section className="roadmap-list" aria-label="Saved roadmaps">
                  <h2 className="roadmap-list__title">Your roadmaps</h2>
                  <ul className="roadmap-list__cards">
                    {roadmaps.map((r) => {
                      const skillCount = r.milestones?.flatMap((m) => m.skills ?? []).length ?? 0;
                      const milestoneCount = r.milestones?.length ?? 0;
                      const selected = selectedId === r.id;
                      return (
                        <li key={r.id}>
                          <button
                            type="button"
                            className={`roadmap-list__card${selected ? " is-selected" : ""}`}
                            onClick={() => {
                              setSelectedId(r.id);
                              setRoadmapSuccess("Roadmap loaded.");
                            }}
                          >
                            <strong>{r.target_role}</strong>
                            <span>
                              {r.pace} pace · {milestoneCount} milestones · {skillCount} skills
                            </span>
                            <span className="roadmap-list__meta">
                              Updated {new Date(r.updated_at).toLocaleDateString()}
                            </span>
                            <em>{selected ? "Viewing" : "Continue"}</em>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </section>

                {detailLoading && (
                  <div style={{ textAlign: "center", padding: "2rem" }}><Spinner size="md" /></div>
                )}
                {detailError && (
                  <div className="roadmap-status-strip__row roadmap-status-strip__row--error roadmap-error" role="alert">
                    <span>Could not load this roadmap detail. Please try again.</span>
                    <Button variant="ghost" size="sm" onClick={() => void refetch()}>Retry</Button>
                  </div>
                )}

                {activeRoadmap && !detailLoading && (
                  <div className="roadmap-detail">
                    {(() => {
                      const savedTaxonomy = extractRoadmapTaxonomy(activeRoadmap.personalization_inputs);
                      if (!savedTaxonomy) return null;
                      const roleText = activeRoadmap.target_role || "";
                      const roleChanged =
                        !!savedTaxonomy.target_role_text &&
                        savedTaxonomy.target_role_text.trim().toLowerCase() !== roleText.trim().toLowerCase() &&
                        !(
                          savedTaxonomy.accepted_by_user &&
                          (savedTaxonomy.matched_role_title || savedTaxonomy.matched_role_id || "")
                            .trim()
                            .toLowerCase() === roleText.trim().toLowerCase()
                        );
                      const detailPhase: RoleIntelPhase = roleChanged
                        ? "ready"
                        : phaseFromTaxonomyMeta(savedTaxonomy, roleText);
                      return (
                        <RoleIntelligenceCard
                          compact
                          phase={detailPhase}
                          roleText={roleText}
                          meta={roleChanged ? null : savedTaxonomy}
                        />
                      );
                    })()}
                    <div className="roadmap-detail-grid feature-grid-2" style={{ marginBottom: "1.5rem" }}>
                      <Card padding="lg" className="feature-glass roadmap-progress-summary">
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                          <div>
                            <p style={{ fontWeight: 700 }}>{activeRoadmap.target_role}</p>
                            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                              {activeRoadmap.pace} pace · {activeRoadmap.starting_skill_level ?? "auto"} level · {activeRoadmap.milestones.length} milestones
                            </p>
                          </div>
                          <p className="roadmap-progress" style={{ fontWeight: 800, fontSize: "1.25rem", color: "var(--accent-violet)" }}>{pct}%</p>
                        </div>
                        <div style={{ height: "8px", borderRadius: "999px", background: "var(--bg-overlay)", overflow: "hidden" }}>
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} style={{ height: "100%", background: "var(--gradient-primary)", borderRadius: "999px" }} />
                        </div>
                        <ul className="roadmap-progress-summary__counts" aria-label="Skill status counts">
                          <li><strong>{counts.completed}</strong> completed</li>
                          <li><strong>{counts.in_progress}</strong> in progress</li>
                          <li><strong>{counts.not_started}</strong> not started</li>
                          <li><strong>{counts.total}</strong> skills total</li>
                        </ul>
                        <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.55rem" }}>
                          Current progress is tracked through roadmap skills.
                          Milestones organize the roadmap; skills are the current actionable progress units.
                          Detailed sub-task tracking comes in a later slice.
                        </p>
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
                          Based on saved skill status for this roadmap
                        </p>
                      </Card>
                    </div>

                    <SkillTracker
                      roadmap={activeRoadmap}
                      onRefresh={() => { void refetch(); void refetchList(); }}
                      onOpenSkill={setSkillDetail}
                      onActionMessage={handleActionMessage}
                    />

                    <AnimatePresence mode="wait">
                      {view === "timeline" ? (
                        <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                          <TimelineView
                            roadmap={activeRoadmap}
                            onRefresh={() => { void refetch(); void refetchList(); }}
                            onOpenSkill={setSkillDetail}
                            onActionMessage={handleActionMessage}
                          />
                        </motion.div>
                      ) : (
                        <motion.div key="kanban" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                          <div className="roadmap-kanban">
                            <KanbanView
                              roadmap={activeRoadmap}
                              onRefresh={() => { void refetch(); void refetchList(); }}
                              onOpenSkill={setSkillDetail}
                              onActionMessage={handleActionMessage}
                            />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </>
            )}
          </div>

          <aside className="roadmap-help" aria-label="What this roadmap can help with">
            <h2>What this roadmap can help with</h2>
            <ul>
              {pathwayExamples.map((ex) => (
                <li key={ex}>{ex}</li>
              ))}
            </ul>
            <p className="roadmap-help__note">
              Progress is based on saved milestones and skills currently available.
              More detailed task tracking comes in a later slice. Specialized pathway engines
              (public sector, study abroad, etc.) are not built in this repair.
            </p>
          </aside>
        </div>

        <p className="roadmap-footnote">
          Career Roadmap is a platform-wide planning tool for every persona — graduates, career switchers,
          and working professionals alike.
        </p>

        <GenerateModal
          open={generateOpen}
          onClose={() => setGenerateOpen(false)}
          onCreated={(created) => { void handleCreated(created); }}
        />
        <SkillDetailModal
          skill={skillDetail}
          roadmapId={activeRoadmap?.id ?? ""}
          open={!!skillDetail}
          onClose={() => setSkillDetail(null)}
          onRefresh={() => { void refetch(); void refetchList(); }}
          onActionMessage={handleActionMessage}
        />
      </div>
    </div>
  );
}
