/**
 * Interview pack display — comprehensive Q&A, per-question study material, PDF export.
 */

import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen, ChevronDown, ChevronUp, CheckCircle, Clock,
  AlertTriangle, MessageSquare, Target, ThumbsUp, Zap, GraduationCap, Download, FileText,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";
import { Spinner } from "../ui/Spinner";
import type { InterviewQuestion, InterviewStudyMaterial } from "../../types/api";

const DIFF_COLOR: Record<string, string> = {
  Easy: "emerald", Medium: "amber", Hard: "rose", Expert: "violet",
};

function parseStudyMaterial(raw: unknown): InterviewStudyMaterial | null {
  if (!raw || typeof raw !== "object") return null;
  const s = raw as Record<string, unknown>;
  return {
    overview: String(s.overview ?? ""),
    what_you_need_to_know_first: (s.what_you_need_to_know_first as string[]) ?? [],
    definitions: (s.definitions as { term: string; definition: string }[]) ?? [],
    skill_explanations: (s.skill_explanations as { skill: string; explanation: string }[]) ?? [],
    principles: (s.principles as string[]) ?? [],
    key_concepts: (s.key_concepts as string[]) ?? [],
    step_by_step_breakdown: (s.step_by_step_breakdown as string[]) ?? [],
    explanations: (s.explanations as string[]) ?? [],
    practical_example: String(s.practical_example ?? ""),
    common_mistakes: (s.common_mistakes as string[]) ?? [],
    how_to_answer_better: (s.how_to_answer_better as string[]) ?? [],
    practice_exercises: (s.practice_exercises as string[]) ?? [],
    revision_notes: (s.revision_notes as string[]) ?? [],
    related_concepts: (s.related_concepts as string[]) ?? [],
    estimated_reading_time_minutes: s.estimated_reading_time_minutes as number | null | undefined,
  };
}

/** Backend returns `questions`; frontend types use `skill_clusters` — normalize both. */
export function normalizeInterviewPack(pack: Record<string, unknown> | null | undefined) {
  if (!pack) return null;

  const rawQuestions = (pack.questions ?? []) as Record<string, unknown>[];
  const clusters = (pack.skill_clusters ?? []) as { skill_name: string; questions: InterviewQuestion[] }[];

  const mapQuestion = (q: Record<string, unknown>): InterviewQuestion => ({
    question_id: q.question_id as string | undefined,
    question: q.question as string,
    category: (q.category as string) ?? "technical",
    difficulty: (q.difficulty as InterviewQuestion["difficulty"]) ?? "Medium",
    related_skills: (q.related_skills as string[]) ?? [],
    model_answer: (q.model_answer as string)
      ?? ((q.ideal_answer_points as string[])?.length
        ? (q.ideal_answer_points as string[]).map((p) => `• ${p}`).join("\n")
        : (q.why_asked as string) ?? ""),
    answer_explanation: q.answer_explanation as string | undefined,
    why_asked: q.why_asked as string | undefined,
    evaluation_criteria: (q.evaluation_criteria as string[]) ?? (q.ideal_answer_points as string[]) ?? [],
    common_mistakes: (q.common_mistakes as string[]) ?? [],
    follow_up_questions: (q.follow_up_questions as string[]) ?? (q.follow_ups as string[]) ?? [],
    estimated_answer_time_minutes: (q.estimated_answer_time_minutes as number) ?? 5,
    skill_tag: q.skill_tag as string | null | undefined,
    study_material: parseStudyMaterial(q.study_material) ?? undefined,
    practice_tasks: (q.practice_tasks as string[]) ?? [],
    revision_notes: (q.revision_notes as string[]) ?? [],
  });

  if (clusters.length > 0) {
    return {
      skill_clusters: clusters,
      confidence: (pack.generation_confidence ?? pack.confidence_score) as number | null,
    };
  }

  const bySkill: Record<string, InterviewQuestion[]> = {};
  for (const q of rawQuestions) {
    const skill = (q.skill_tag as string) || (q.category as string) || "General";
    if (!bySkill[skill]) bySkill[skill] = [];
    bySkill[skill].push(mapQuestion(q));
  }

  return {
    skill_clusters: Object.entries(bySkill).map(([skill_name, questions]) => ({ skill_name, questions })),
    confidence: (pack.confidence_score ?? pack.generation_confidence) as number | null,
  };
}

function StudyMaterialPanel({ material }: { material: InterviewStudyMaterial }) {
  const section = (_title: string, children: ReactNode) => (
    <div style={{ marginBottom: "0.75rem" }}>{children}</div>
  );
  return (
    <div className="interview-study-panel">
      {material.overview && (
        <p style={{ fontSize: "0.82rem", lineHeight: 1.65, color: "var(--text-primary)", marginBottom: "0.75rem" }}>
          {material.overview}
        </p>
      )}
      {material.what_you_need_to_know_first && material.what_you_need_to_know_first.length > 0 && section("first", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>What you need to know first</p>
          {material.what_you_need_to_know_first.map((item, i) => (
            <p key={i} style={{ fontSize: "0.78rem", marginBottom: "0.25rem" }}>• {item}</p>
          ))}
        </>
      ))}
      {material.definitions?.length > 0 && section("defs", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Definitions</p>
          {material.definitions.map((d, i) => (
            <div key={i} style={{ fontSize: "0.78rem", marginBottom: "0.35rem" }}>
              <strong>{d.term}:</strong> {d.definition}
            </div>
          ))}
        </>
      ))}
      {material.skill_explanations && material.skill_explanations.length > 0 && section("skills", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Skill-by-skill</p>
          {material.skill_explanations.map((se, i) => (
            <p key={i} style={{ fontSize: "0.78rem", marginBottom: "0.35rem" }}><strong>{se.skill}:</strong> {se.explanation}</p>
          ))}
        </>
      ))}
      {material.step_by_step_breakdown && material.step_by_step_breakdown.length > 0 && section("steps", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Step-by-step</p>
          {material.step_by_step_breakdown.map((step, i) => (
            <p key={i} style={{ fontSize: "0.78rem", marginBottom: "0.25rem" }}>{i + 1}. {step}</p>
          ))}
        </>
      ))}
      {material.principles?.length > 0 && section("principles", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Principles</p>
          {material.principles.map((p, i) => (
            <div key={i} style={{ display: "flex", gap: "6px", fontSize: "0.78rem", marginBottom: "0.25rem" }}>
              <CheckCircle size={11} style={{ color: "var(--accent-emerald)", marginTop: 3, flexShrink: 0 }} />{p}
            </div>
          ))}
        </>
      ))}
      {material.practical_example && section("example", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Practical example</p>
          <p style={{ fontSize: "0.78rem", lineHeight: 1.55 }}>{material.practical_example}</p>
        </>
      ))}
      {material.how_to_answer_better && material.how_to_answer_better.length > 0 && section("answer", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>How to answer better</p>
          {material.how_to_answer_better.map((h, i) => <p key={i} style={{ fontSize: "0.78rem" }}>• {h}</p>)}
        </>
      ))}
      {material.practice_exercises && material.practice_exercises.length > 0 && section("practice", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Practice exercises</p>
          {material.practice_exercises.map((ex, i) => <p key={i} style={{ fontSize: "0.78rem" }}>• {ex}</p>)}
        </>
      ))}
      {material.revision_notes && material.revision_notes.length > 0 && section("revision", (
        <>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Quick revision</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
            {material.revision_notes.map((n) => <Badge key={n} color="cyan" size="sm">{n}</Badge>)}
          </div>
        </>
      ))}
      {material.key_concepts?.length > 0 && (
        <div style={{ marginBottom: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
          {material.key_concepts.map((c) => <Badge key={c} color="violet" size="sm">{c}</Badge>)}
        </div>
      )}
      {material.explanations?.length > 0 && (
        <div>
          <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "var(--accent-violet)", textTransform: "uppercase", marginBottom: "0.35rem" }}>Explanations</p>
          {material.explanations.map((ex, i) => (
            <p key={i} style={{ fontSize: "0.78rem", lineHeight: 1.55, marginBottom: "0.35rem", color: "var(--text-secondary)" }}>{ex}</p>
          ))}
        </div>
      )}
      {material.estimated_reading_time_minutes != null && (
        <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
          <Clock size={10} style={{ display: "inline", marginRight: 4 }} />
          ~{material.estimated_reading_time_minutes} min read
        </p>
      )}
    </div>
  );
}

function QuestionCard({ q, index }: { q: InterviewQuestion; index: number }) {
  const [open, setOpen] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [studyOpen, setStudyOpen] = useState(false);
  const hasStudy = !!(q.study_material?.overview || q.study_material?.definitions?.length);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      style={{
        borderRadius: "14px", border: "1px solid var(--border-subtle)", overflow: "hidden",
        marginBottom: "0.75rem", background: "var(--bg-glass)", backdropFilter: "blur(12px)",
      }}
    >
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", padding: "1rem 1.25rem", display: "flex", alignItems: "flex-start", gap: "0.75rem",
          background: "none", border: "none", cursor: "pointer", textAlign: "left",
          borderBottom: open ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <span style={{
          width: "22px", height: "22px", borderRadius: "50%", background: "var(--bg-overlay)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "0.7rem", color: "var(--text-secondary)", flexShrink: 0,
        }}>{index + 1}</span>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 600, fontSize: "0.875rem", lineHeight: 1.5, marginBottom: "0.4rem" }}>{q.question}</p>
          {q.why_asked && (
            <p style={{ fontSize: "0.72rem", color: "var(--text-secondary)", marginBottom: "0.4rem", lineHeight: 1.45 }}>
              {q.why_asked}
            </p>
          )}
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            <Badge color={DIFF_COLOR[q.difficulty] as any ?? "default"} size="sm">{q.difficulty}</Badge>
            <Badge color="default" size="sm">{q.category}</Badge>
            <Badge color="default" size="sm"><Clock size={10} /> ~{q.estimated_answer_time_minutes}m</Badge>
            {hasStudy && <Badge color="cyan" size="sm"><GraduationCap size={10} /> Study material</Badge>}
          </div>
        </div>
        {open ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: "hidden" }}>
            <div style={{ padding: "1.25rem" }}>
              {hasStudy && (
                <div style={{ marginBottom: "1rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                    <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--accent-cyan)", textTransform: "uppercase" }}>
                      <GraduationCap size={12} style={{ display: "inline", marginRight: 4 }} />
                      Study material (zero prior knowledge)
                    </p>
                    <Button variant={studyOpen ? "primary" : "secondary"} size="sm" onClick={() => setStudyOpen(!studyOpen)}>
                      {studyOpen ? "Hide study guide" : "Open study guide"}
                    </Button>
                  </div>
                  <AnimatePresence>
                    {studyOpen && q.study_material && (
                      <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
                        <StudyMaterialPanel material={q.study_material} />
                      </motion.div>
                    )}
                  </AnimatePresence>
                  {!studyOpen && (
                    <p style={{ fontSize: "0.72rem", color: "var(--text-secondary)" }}>
                      Read definitions, principles, and explanations before revealing the model answer.
                    </p>
                  )}
                </div>
              )}

              <div style={{ marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase" }}>
                    <ThumbsUp size={11} style={{ marginRight: 4 }} />Model answer
                  </p>
                  {!revealed && <Button variant="ghost" size="sm" onClick={() => setRevealed(true)}>Reveal answer</Button>}
                </div>
                {revealed ? (
                  <div style={{ padding: "0.875rem", borderRadius: "10px", background: "rgba(139,92,246,0.05)", border: "1px solid rgba(139,92,246,0.15)", fontSize: "0.8rem", lineHeight: 1.65, whiteSpace: "pre-wrap" }}>
                    {q.model_answer}
                  </div>
                ) : (
                  <div style={{ padding: "0.875rem", borderRadius: "10px", background: "var(--bg-overlay)", filter: "blur(4px)", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                    {q.model_answer.slice(0, 120)}…
                  </div>
                )}
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                {q.evaluation_criteria?.length > 0 && (
                  <div>
                    <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                      <Target size={11} style={{ marginRight: 4 }} />What interviewers look for
                    </p>
                    {q.evaluation_criteria.map((c, i) => (
                      <div key={i} style={{ display: "flex", gap: "6px", marginBottom: "3px", fontSize: "0.78rem" }}>
                        <CheckCircle size={11} style={{ color: "var(--accent-emerald)", marginTop: 3, flexShrink: 0 }} />{c}
                      </div>
                    ))}
                  </div>
                )}
                {q.common_mistakes?.length > 0 && (
                  <div>
                    <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                      <AlertTriangle size={11} style={{ marginRight: 4 }} />Common mistakes
                    </p>
                    {q.common_mistakes.map((m, i) => (
                      <div key={i} style={{ display: "flex", gap: "6px", marginBottom: "3px", fontSize: "0.78rem" }}>
                        <AlertTriangle size={11} style={{ color: "var(--accent-amber)", marginTop: 3, flexShrink: 0 }} />{m}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {q.follow_up_questions?.length > 0 && (
                <div style={{ marginTop: "0.875rem" }}>
                  <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                    <MessageSquare size={11} style={{ marginRight: 4 }} />Follow-ups
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

interface InterviewPackViewProps {
  pack: Record<string, unknown> | null | undefined;
  loading?: boolean;
  generating?: boolean;
  jobTitle?: string;
  jobId?: string | null;
  onRegenerate?: () => void;
  onDownloadPdf?: (format?: "pdf" | "study_material" | "questions_answers") => void;
  downloadingPdf?: boolean;
}

export function InterviewPackView({
  pack, loading, generating, jobTitle, jobId, onRegenerate, onDownloadPdf, downloadingPdf,
}: InterviewPackViewProps) {
  const normalized = normalizeInterviewPack(pack);
  const clusters = normalized?.skill_clusters ?? [];
  const totalQuestions = clusters.reduce((a, c) => a + c.questions.length, 0);
  const roleOverview = pack?.role_overview as Record<string, unknown> | undefined;
  const libraryStatus = pack?.library_status as string | undefined;
  const fallbackMessage = pack?.fallback_message as string | undefined;
  const extractionWarnings = [
    ...((pack?.job_posting_extraction as { warnings?: string[] } | undefined)?.warnings ?? []),
    ...((pack?.job_intelligence as { warnings?: string[] } | undefined)?.warnings ?? []),
  ].filter((w, i, arr) => arr.indexOf(w) === i);
  const extractionConfidence = (pack?.job_posting_extraction as { extraction_confidence?: string } | undefined)?.extraction_confidence;
  let questionIndex = 0;

  if (loading || generating) {
    return (
      <div className="feature-glass feature-panel" style={{ textAlign: "center", padding: "3rem" }}>
        <Spinner size="lg" />
        <p style={{ marginTop: "1rem", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
          {generating ? "AI agents generating comprehensive Q&A and study material…" : "Loading interview pack…"}
        </p>
      </div>
    );
  }

  if (!normalized || clusters.length === 0) {
    return (
      <div className="feature-glass feature-panel" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
        <BookOpen size={48} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
        <p style={{ fontWeight: 600 }}>No interview pack yet</p>
        <p style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
          Fill in the job details above and click <strong>Generate interview pack</strong>.
          Each question includes study material for zero prior knowledge and a model answer.
        </p>
        {jobId && onRegenerate && (
          <div style={{ marginTop: "1.25rem" }}>
            <Button variant="primary" size="sm" leftIcon={<Zap size={14} />} onClick={onRegenerate}>
              Regenerate interview pack
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="feature-glass feature-panel" id="interview-pack-section">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.25rem" }}>
        <div>
          <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.1rem", marginBottom: "0.25rem" }}>
            Interview pack{jobTitle ? ` — ${jobTitle}` : ""}
          </h2>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
            Comprehensive questions, model answers, and beginner study guides — generated by the multi-agent pipeline.
          </p>
          {typeof roleOverview?.summary === "string" && roleOverview.summary && (
            <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: "0.5rem", lineHeight: 1.5 }}>
              {roleOverview.summary}
            </p>
          )}
          {fallbackMessage && (
            <p style={{ fontSize: "0.75rem", color: "var(--accent-amber)", marginBottom: "0.5rem" }}>{fallbackMessage}</p>
          )}
          {extractionConfidence && extractionConfidence !== "failed" && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.35rem" }}>
              Job link extraction: {extractionConfidence} confidence
            </p>
          )}
          {extractionWarnings.slice(0, 3).map((warning) => (
            <p key={warning} style={{ fontSize: "0.75rem", color: "var(--accent-amber)", marginBottom: "0.35rem", lineHeight: 1.45 }}>
              {warning}
            </p>
          ))}
          {libraryStatus === "library_fallback" && (
            <Badge color="amber" size="sm">Loaded from saved documents</Badge>
          )}
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            <Badge color="violet">{totalQuestions} questions</Badge>
            <Badge color="default">{clusters.length} skill areas</Badge>
            <Badge color="cyan">Study material included</Badge>
            {normalized.confidence != null && (
              <Badge color={normalized.confidence > 0.8 ? "emerald" : "amber"}>
                {Math.round(normalized.confidence * 100)}% confidence
              </Badge>
            )}
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {jobId && onDownloadPdf && (
            <>
              <Button variant="secondary" size="sm" leftIcon={<Download size={14} />} onClick={() => onDownloadPdf("pdf")} loading={downloadingPdf} disabled={!jobId}>
                Full pack PDF
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<GraduationCap size={14} />} onClick={() => onDownloadPdf("study_material")} disabled={!jobId}>
                Study PDF
              </Button>
              <Button variant="ghost" size="sm" leftIcon={<FileText size={14} />} onClick={() => onDownloadPdf("questions_answers")} disabled={!jobId}>
                Q&A PDF
              </Button>
            </>
          )}
          {onRegenerate && (
            <Button variant="secondary" size="sm" leftIcon={<Zap size={14} />} onClick={onRegenerate}>
              Regenerate
            </Button>
          )}
        </div>
      </div>

      {clusters.map((cluster) => {
        const node = (
          <Card key={cluster.skill_name} padding="none" style={{ marginBottom: "1rem", overflow: "hidden" }}>
            <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <BookOpen size={16} style={{ color: "var(--accent-violet)" }} />
              <span style={{ fontWeight: 700, flex: 1 }}>{cluster.skill_name}</span>
              <Badge color="violet" size="sm">{cluster.questions.length}q</Badge>
            </div>
            <div style={{ padding: "1rem 1.25rem" }}>
              {cluster.questions.map((q, i) => {
                const card = <QuestionCard key={i} q={q} index={questionIndex + i} />;
                return card;
              })}
            </div>
          </Card>
        );
        questionIndex += cluster.questions.length;
        return node;
      })}
    </div>
  );
}
