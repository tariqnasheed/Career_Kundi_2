/**
 * InterviewPackPage.tsx
 * =====================
 * Generate and review AI interview packs for saved jobs.
 * Shows skill clusters, individual questions with model answers,
 * difficulty badges, follow-up questions, and evaluation criteria.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen, Zap, ChevronDown, ChevronUp, CheckCircle,
  Clock, AlertTriangle, MessageSquare, Target, ThumbsUp,
} from "lucide-react";
import { jobApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { InterviewPackRead, SavedJobRead, InterviewQuestion } from "../types/api";

// ─── Difficulty config ─────────────────────────────────────────────────────
const DIFF_COLOR: Record<string, string> = {
  Easy:   "emerald",
  Medium: "amber",
  Hard:   "rose",
  Expert: "violet",
};

// ─── Individual question card ──────────────────────────────────────────────
function QuestionCard({ q, index }: { q: InterviewQuestion; index: number }) {
  const [open, setOpen] = useState(false);
  const [revealed, setRevealed] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      style={{
        borderRadius: "14px",
        border: "1px solid var(--border-subtle)",
        overflow: "hidden",
        marginBottom: "0.75rem",
        background: "var(--bg-glass)", backdropFilter: "blur(12px)",
      }}
    >
      {/* Question header */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", padding: "1rem 1.25rem",
          display: "flex", alignItems: "flex-start", gap: "0.75rem",
          background: "none", border: "none", cursor: "pointer", textAlign: "left",
          borderBottom: open ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <span style={{
          width: "22px", height: "22px", borderRadius: "50%",
          background: "var(--bg-overlay)", display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "0.7rem", color: "var(--text-secondary)", flexShrink: 0, marginTop: "1px",
        }}>
          {index + 1}
        </span>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 600, fontSize: "0.875rem", lineHeight: 1.5, marginBottom: "0.4rem" }}>{q.question}</p>
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            <Badge color={DIFF_COLOR[q.difficulty] as any ?? "default"} size="sm">{q.difficulty}</Badge>
            <Badge color="default" size="sm">{q.category}</Badge>
            <Badge color="default" size="sm"><Clock size={10} /> ~{q.estimated_answer_time_minutes}m</Badge>
          </div>
        </div>
        {open ? <ChevronUp size={15} style={{ color: "var(--text-secondary)", flexShrink: 0 }} /> : <ChevronDown size={15} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />}
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: "hidden" }}
          >
            <div style={{ padding: "1.25rem" }}>
              {/* Model answer (hidden until revealed) */}
              <div style={{ marginBottom: "1.25rem" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
                    <ThumbsUp size={11} style={{ marginRight: "4px" }} />Model answer
                  </p>
                  {!revealed && (
                    <Button variant="ghost" size="sm" onClick={() => setRevealed(true)}>
                      Reveal answer
                    </Button>
                  )}
                </div>
                {revealed ? (
                  <div style={{
                    padding: "0.875rem", borderRadius: "10px",
                    background: "rgba(139,92,246,0.05)", border: "1px solid rgba(139,92,246,0.15)",
                    fontSize: "0.8rem", lineHeight: 1.65, color: "var(--text-primary)",
                  }}>
                    {q.model_answer}
                  </div>
                ) : (
                  <div style={{
                    padding: "0.875rem", borderRadius: "10px",
                    background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)",
                    filter: "blur(4px)", pointerEvents: "none", fontSize: "0.8rem", lineHeight: 1.65,
                    color: "var(--text-secondary)", userSelect: "none",
                  }}>
                    {q.model_answer.slice(0, 120)}…
                  </div>
                )}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                {/* Evaluation criteria */}
                {q.evaluation_criteria?.length > 0 && (
                  <div>
                    <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.4rem" }}>
                      <Target size={11} style={{ marginRight: "4px" }} />What interviewers look for
                    </p>
                    {q.evaluation_criteria.map((c, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "6px", marginBottom: "3px", fontSize: "0.78rem" }}>
                        <CheckCircle size={11} style={{ color: "var(--accent-emerald)", marginTop: "3px", flexShrink: 0 }} />
                        {c}
                      </div>
                    ))}
                  </div>
                )}

                {/* Common mistakes */}
                {q.common_mistakes?.length > 0 && (
                  <div>
                    <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.4rem" }}>
                      <AlertTriangle size={11} style={{ marginRight: "4px" }} />Common mistakes
                    </p>
                    {q.common_mistakes.map((m, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: "6px", marginBottom: "3px", fontSize: "0.78rem" }}>
                        <AlertTriangle size={11} style={{ color: "var(--accent-amber)", marginTop: "3px", flexShrink: 0 }} />
                        {m}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Follow-up questions */}
              {q.follow_up_questions?.length > 0 && (
                <div style={{ marginTop: "0.875rem" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.5rem" }}>
                    <MessageSquare size={11} style={{ marginRight: "4px" }} />Follow-up questions
                  </p>
                  {q.follow_up_questions.map((fq, i) => (
                    <div key={i} style={{ padding: "0.4rem 0.75rem", borderRadius: "6px", background: "var(--bg-overlay)", marginBottom: "0.35rem", fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                      → {fq}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ─── Skill cluster ─────────────────────────────────────────────────────────
function SkillCluster({ cluster, startIndex }: { cluster: { skill_name: string; questions: InterviewQuestion[] }; startIndex: number }) {
  const [open, setOpen] = useState(true);

  return (
    <Card padding="none" style={{ marginBottom: "1.25rem", overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: "0.75rem",
          padding: "1rem 1.25rem", background: "none", border: "none", cursor: "pointer",
          borderBottom: open ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <BookOpen size={16} style={{ color: "var(--accent-violet)" }} />
        <span style={{ fontWeight: 700, flex: 1, textAlign: "left" }}>{cluster.skill_name}</span>
        <Badge color="violet" size="sm">{cluster.questions.length}q</Badge>
        {open ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
      </button>
      {open && (
        <div style={{ padding: "1rem 1.25rem" }}>
          {cluster.questions.map((q, i) => (
            <QuestionCard key={i} q={q} index={startIndex + i} />
          ))}
        </div>
      )}
    </Card>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────
export default function InterviewPackPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const { data: jobs, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => jobApi.list(),
  });

  const { data: pack, isLoading: packLoading, refetch: refetchPack } = useQuery({
    queryKey: ["interview-pack", selectedJobId],
    queryFn: () => jobApi.getInterviewPack(selectedJobId!),
    enabled: !!selectedJobId,
  });

  const generateMutation = useMutation({
    mutationFn: () => jobApi.generateInterviewPack(selectedJobId!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["interview-pack", selectedJobId] });
      addToast({ type: "success", title: "Interview pack ready!", message: "AI-generated questions, model answers, and evaluation criteria are ready." });
    },
    onError: () => addToast({ type: "error", message: "Generation failed. Try again." }),
  });

  const totalQuestions = pack?.skill_clusters?.reduce((a: number, c: any) => a + c.questions.length, 0) ?? 0;
  let questionIndex = 0;

  if (jobsLoading) return <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}><Spinner size="lg" /></div>;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.25rem" }}>Interview Prep</h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", fontSize: "0.875rem" }}>
          AI-generated question banks with model answers, evaluation criteria, and follow-up questions.
        </p>

        {/* Job selector */}
        <Card padding="lg" style={{ marginBottom: "1.5rem" }}>
          <CardHeader><CardTitle>Select a job</CardTitle></CardHeader>
          <CardContent>
            {!jobs?.length ? (
              <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>No saved jobs. Go to Job Search to import a job first.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                {jobs.map((job: SavedJobRead) => (
                  <button
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    style={{
                      display: "flex", alignItems: "center", gap: "1rem",
                      padding: "0.75rem 1rem", borderRadius: "10px",
                      border: selectedJobId === job.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                      background: selectedJobId === job.id ? "rgba(139,92,246,0.05)" : "var(--bg-overlay)",
                      cursor: "pointer", textAlign: "left",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <p style={{ fontWeight: 600, fontSize: "0.875rem" }}>{job.title}</p>
                      <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{job.company_name}</p>
                    </div>
                    {selectedJobId === job.id && <CheckCircle size={16} style={{ color: "var(--accent-violet)" }} />}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {selectedJobId && (
          <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.5rem" }}>
            <Button
              variant="primary"
              leftIcon={<Zap size={15} />}
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
            >
              {pack ? "Regenerate interview pack" : "Generate interview pack"}
            </Button>
            {pack && (
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Badge color="violet">{totalQuestions} questions</Badge>
                <Badge color="default">{pack.skill_clusters?.length ?? 0} skill areas</Badge>
                {pack.generation_confidence && (
                  <Badge color={pack.generation_confidence > 0.8 ? "emerald" : "amber"}>
                    {Math.round(pack.generation_confidence * 100)}% confidence
                  </Badge>
                )}
              </div>
            )}
          </div>
        )}

        {/* Interview pack content */}
        {packLoading && <div style={{ textAlign: "center", padding: "3rem" }}><Spinner size="lg" /></div>}

        {pack && !packLoading && (
          <AnimatePresence>
            {pack.skill_clusters?.map((cluster: any) => {
              const node = <SkillCluster key={cluster.skill_name} cluster={cluster} startIndex={questionIndex} />;
              questionIndex += cluster.questions.length;
              return node;
            })}
          </AnimatePresence>
        )}

        {!pack && !packLoading && selectedJobId && (
          <div style={{ textAlign: "center", padding: "4rem", color: "var(--text-secondary)" }}>
            <BookOpen size={48} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
            <p>No interview pack yet for this job.</p>
            <p style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>Click "Generate interview pack" above.</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
