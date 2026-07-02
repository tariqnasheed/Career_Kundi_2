/**
 * JobSearchPage.tsx
 * Unified job search + interview prep — import or fill job details,
 * save jobs, generate interview packs, and manage applications on one page.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Link2, FileText, Zap,
  MapPin, Building,
  Clock, ExternalLink, Search,
  Globe, Briefcase, Target, TrendingUp, X, BookOpen,
} from "lucide-react";
import { applyApi, jobApi, cvApi, profileApi } from "../lib/api";
import { EMPTY_JOB_FORM, formToSavePayload, jobToForm } from "../lib/jobForm";
import { popularRoleToForm, savePayloadFromPopularRole, type PopularJobRole } from "../lib/popularJobRoles";
import type { JobFormState } from "../lib/jobForm";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "../components/ui/Modal";
import { Spinner } from "../components/ui/Spinner";
import { MatchScoreRing } from "../components/features/MatchScoreRing";
import { DefaultCVSelector, getDefaultCvId } from "../components/features/DefaultCVSelector";
import { JobDiscoveryPanel } from "../components/features/JobDiscoveryPanel";
import { PopularJobRolesPanel } from "../components/features/PopularJobRolesPanel";
import { JobDetailsForm } from "../components/features/JobDetailsForm";
import { InterviewPackView, normalizeInterviewPack } from "../components/features/InterviewPackView";
import { useUIStore } from "../store/ui";
import type { ExtractedSkill, GeneratedCVRead, SavedJobRead, ApiError } from "../types/api";

// ─── Match rating helpers ───────────────────────────────────────────────────

function normSkill(s: string) {
  return s.trim().toLowerCase();
}

function buildMatchBreakdown(job: SavedJobRead, userSkills: string[]) {
  const userSet = new Set(userSkills.map(normSkill));
  const jobSkills = job.extracted_skills ?? [];
  const matched: ExtractedSkill[] = [];
  const missing: ExtractedSkill[] = [];

  for (const sk of jobSkills) {
    const name = sk.skill ?? "";
    if (!name) continue;
    if (userSet.has(normSkill(name))) matched.push(sk);
    else missing.push(sk);
  }

  const transferable = missing.filter(
    (sk) => sk.category === "soft" || sk.importance === "nice-to-have"
  );

  return { matched, missing, transferable, score: job.match_score };
}

function MatchRatingPanel({ job, userSkills }: { job: SavedJobRead; userSkills: string[] }) {
  const { matched, missing, transferable, score } = buildMatchBreakdown(job, userSkills);
  const pct = score ?? 0;
  const color = pct >= 80 ? "emerald" : pct >= 60 ? "amber" : "rose";

  return (
    <Card padding="md" style={{ marginTop: "1rem", borderColor: "var(--border-default)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <Target size={16} style={{ color: "var(--accent-violet)" }} />
          <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>Profile Match Rating</span>
        </div>
        {score != null ? (
          <Badge color={color as any} size="md">{Math.round(score)}% fit</Badge>
        ) : (
          <Badge color="default" size="sm">Not rated</Badge>
        )}
      </div>

      {score != null && (
        <div style={{ height: "6px", borderRadius: "999px", background: "var(--bg-overlay)", marginBottom: "0.75rem", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, background: `var(--accent-${color})`, borderRadius: "999px" }} />
        </div>
      )}

      <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.75rem", lineHeight: 1.5 }}>
        {score != null
          ? `You match ${matched.length} of ${(job.extracted_skills ?? []).length} required skills. Score weights critical skills more heavily than nice-to-haves.`
          : "Add skills to your profile and import a job with listed requirements to see your fit score."}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
        {matched.length > 0 && (
          <div>
            <p style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--accent-emerald)", marginBottom: "0.35rem" }}>Skills match ({matched.length})</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {matched.slice(0, 8).map((s) => (
                <Badge key={s.skill} color="emerald" size="sm">{s.skill}</Badge>
              ))}
            </div>
          </div>
        )}
        {missing.length > 0 && (
          <div>
            <p style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--accent-rose)", marginBottom: "0.35rem" }}>Missing skills ({missing.length})</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {missing.slice(0, 8).map((s) => (
                <Badge key={s.skill} color="rose" size="sm">{s.skill}</Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {missing.length > 0 && (
        <div style={{ marginTop: "0.75rem", padding: "0.625rem", borderRadius: "8px", background: "rgba(139,92,246,0.06)", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <TrendingUp size={12} style={{ display: "inline", marginRight: "4px" }} />
          Suggested action: generate a career roadmap to close gaps in{" "}
          <strong>{missing.slice(0, 3).map((s) => s.skill).join(", ")}</strong>
          {missing.length > 3 ? "…" : ""}.
        </div>
      )}
    </Card>
  );
}

// ─── Saved job card ─────────────────────────────────────────────────────────

const STATUS_OPTIONS: SavedJobRead["status"][] = ["saved", "applied", "interviewing", "offered", "rejected"];

function SavedJobCard({
  job, userSkills, selected, onSelect, onAutoApply, onLoad, onViewPack, onRegeneratePack, isActive,
}: {
  job: SavedJobRead;
  userSkills: string[];
  selected?: boolean;
  onSelect?: (checked: boolean) => void;
  onAutoApply?: () => void;
  onLoad: () => void;
  onViewPack?: () => void;
  onRegeneratePack?: () => void;
  isActive?: boolean;
}) {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { addToast } = useUIStore();
  const [showMatch, setShowMatch] = useState(false);
  const [hovered, setHovered] = useState(false);

  const statusMutation = useMutation({
    mutationFn: (status: SavedJobRead["status"]) => jobApi.updateStatus(job.id, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["jobs"] }); addToast({ type: "success", message: "Status updated." }); },
  });

  const deleteMutation = useMutation({
    mutationFn: () => jobApi.delete(job.id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["jobs"] }); addToast({ type: "info", message: "Job removed." }); },
  });

  const previewSnippet = job.description_raw?.slice(0, 180) ?? job.responsibilities?.[0] ?? "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`feature-glass feature-glass--lift job-card-premium${isActive ? " job-card-premium--active" : ""}`}
      style={isActive ? { borderColor: "var(--accent-violet)", boxShadow: "var(--shadow-violet)" } : undefined}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {onSelect && (
        <input type="checkbox" checked={selected} onChange={(e) => onSelect(e.target.checked)} aria-label={`Select ${job.title}`} style={{ marginTop: 4, accentColor: "var(--accent-violet)" }} />
      )}
      <div className="job-card-premium__logo">{(job.company_name ?? "?")[0].toUpperCase()}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "0.75rem" }}>
          <div>
            <p style={{ fontWeight: 700, fontFamily: "var(--font-heading)", marginBottom: "2px" }}>{job.title}</p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              {job.company_name}{job.location ? ` · ${job.location}` : ""}
              {job.employment_type ? ` · ${job.employment_type}` : ""}
            </p>
          </div>
          <MatchScoreRing score={job.match_score} />
        </div>
        <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
          {job.is_remote && <Badge color="emerald" size="sm">Remote</Badge>}
          {job.source_url && <Badge color="default" size="sm">{(() => { try { return new URL(job.source_url!).hostname.replace("www.", ""); } catch { return "Source"; } })()}</Badge>}
          {Boolean(job.has_interview_pack) && <Badge color="violet" size="sm">Pack ready</Badge>}
          {!job.has_interview_pack && job.interview_pack_generated_at && (
            <Badge color="amber" size="sm">Pack incomplete</Badge>
          )}
        </div>
        {hovered && previewSnippet && (
          <div className="job-card-premium__hover-preview">{previewSnippet}…</div>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "flex-end" }}>
        <select
          value={job.status}
          onChange={(e) => statusMutation.mutate(e.target.value as SavedJobRead["status"])}
          style={{
            padding: "0.35rem 0.5rem", borderRadius: "8px", fontSize: "0.75rem",
            background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)",
          }}
        >
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div style={{ gridColumn: "1 / -1", display: "flex", gap: "0.5rem", marginTop: "0.25rem", flexWrap: "wrap" }}>
        <Button variant={isActive ? "primary" : "ghost"} size="sm" onClick={onLoad}>Edit & prep</Button>
        {Boolean(job.has_interview_pack) && onViewPack && (
          <Button variant="secondary" size="sm" leftIcon={<BookOpen size={12} />} onClick={onViewPack}>
            Open interview pack
          </Button>
        )}
        {!job.has_interview_pack && job.interview_pack_generated_at && onRegeneratePack && (
          <Button variant="secondary" size="sm" leftIcon={<Zap size={12} />} onClick={onRegeneratePack}>
            Regenerate pack
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={() => setShowMatch(!showMatch)}>Match breakdown</Button>
        <Button variant="ghost" size="sm" onClick={() => navigate(`/cv-builder?jobId=${job.id}`)}>Build CV</Button>
        {onAutoApply && <Button variant="secondary" size="sm" leftIcon={<Zap size={12} />} onClick={onAutoApply}>Auto Apply</Button>}
        {job.source_url && (
          <Button variant="ghost" size="sm" leftIcon={<ExternalLink size={12} />} onClick={() => window.open(job.source_url!, "_blank")}>
            Original
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate()} style={{ marginLeft: "auto", color: "var(--accent-rose)" }}>
          <X size={14} />
        </Button>
      </div>

      {showMatch && <div style={{ gridColumn: "1 / -1" }}><MatchRatingPanel job={job} userSkills={userSkills} /></div>}
    </motion.div>
  );
}

// ─── Auto Apply Modal (unchanged core logic) ──────────────────────────────

function AutoApplyModal({ job, open, onClose }: { job: SavedJobRead | null; open: boolean; onClose: () => void }) {
  const { addToast } = useUIStore();
  const { data: cvs } = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });

  const [step, setStep] = useState<"select" | "review" | "submitting" | "done" | "blocked">("select");
  const [selectedCvId, setSelectedCvId] = useState("");
  const [coverLetterRequested, setCoverLetterRequested] = useState(false);
  const [applicationId, setApplicationId] = useState("");
  const [result, setResult] = useState<any>(null);

  const startMutation = useMutation({
    mutationFn: () => applyApi.startApply(job?.id || "temp", {
      cv_id: selectedCvId || undefined,
      cover_letter_requested: coverLetterRequested,
    }),
    onSuccess: (data: any) => { setApplicationId(data.id); setStep("review"); },
  });

  const confirmMutation = useMutation({
    mutationFn: () => applyApi.confirm(applicationId),
    onSuccess: (data: any) => {
      setResult(data);
      setStep(data.status === "submitted" ? "done" : data.status === "blocked" ? "blocked" : "done");
    },
    onError: () => { addToast({ type: "error", message: "Application failed." }); setStep("blocked"); },
  });

  const reset = () => {
    setStep("select"); setSelectedCvId(""); setCoverLetterRequested(false);
    setApplicationId(""); setResult(null); onClose();
  };

  if (!job) return null;

  return (
    <Modal open={open} onClose={reset} title="Auto Apply" size="md">
      <ModalBody>
        {step === "select" && (
          <div>
            <div style={{ padding: "0.75rem", borderRadius: "10px", background: "rgba(139,92,246,0.08)", marginBottom: "1.25rem" }}>
              <p style={{ fontWeight: 600, fontSize: "0.875rem" }}>{job.title}</p>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{job.company_name}</p>
            </div>
            <select value={selectedCvId} onChange={(e) => setSelectedCvId(e.target.value)} style={{ width: "100%", padding: "0.625rem", borderRadius: "10px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", marginBottom: "1rem" }}>
              <option value="">Use profile data (no CV file)</option>
              {cvs?.map((cv: GeneratedCVRead) => <option key={cv.id} value={cv.id}>{cv.name || cv.template}</option>)}
            </select>
            <label style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer" }}>
              <input type="checkbox" checked={coverLetterRequested} onChange={(e) => setCoverLetterRequested(e.target.checked)} />
              <span style={{ fontSize: "0.875rem" }}>Generate a tailored cover letter</span>
            </label>
          </div>
        )}
        {step === "review" && <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>Confirm submission for {job.title} at {job.company_name}.</p>}
        {step === "submitting" && <div style={{ textAlign: "center", padding: "2rem" }}><Spinner size="lg" /></div>}
        {step === "done" && <p style={{ textAlign: "center", color: "var(--accent-emerald)" }}>Application submitted!</p>}
        {step === "blocked" && <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>Auto-apply blocked for this platform. Use the original posting link.</p>}
      </ModalBody>
      <ModalFooter>
        {step === "select" && (
          <>
            <Button variant="ghost" onClick={reset}>Cancel</Button>
            <Button variant="primary" onClick={() => startMutation.mutate()} loading={startMutation.isPending}>Review & Continue</Button>
          </>
        )}
        {step === "review" && (
          <>
            <Button variant="ghost" onClick={() => setStep("select")}>Back</Button>
            <Button variant="primary" onClick={() => { setStep("submitting"); confirmMutation.mutate(); }} loading={confirmMutation.isPending}>Confirm & Submit</Button>
          </>
        )}
        {(step === "done" || step === "blocked") && <Button variant="primary" onClick={reset}>Done</Button>}
      </ModalFooter>
    </Modal>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────

export default function JobSearchPage() {
  const [searchParamsUrl] = useSearchParams();
  const packSectionRef = useRef<HTMLDivElement>(null);
  const jobFormRef = useRef<HTMLDivElement>(null);
  const skipPackClearRef = useRef(false);
  const [jobForm, setJobForm] = useState<JobFormState>(EMPTY_JOB_FORM);
  const [activeJobId, setActiveJobId] = useState<string | null>(searchParamsUrl.get("jobId"));
  const [applyJob, setApplyJob] = useState<SavedJobRead | null>(null);
  const [applyOpen, setApplyOpen] = useState(false);
  const [savedFilter, setSavedFilter] = useState("");
  const [defaultCvId, setDefaultCvId] = useState(getDefaultCvId() ?? "");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectingRoleId, setSelectingRoleId] = useState<string | null>(null);
  const [packOverride, setPackOverride] = useState<Record<string, unknown> | null>(null);
  const qc = useQueryClient();
  const { addToast } = useUIStore();
  const navigate = useNavigate();

  const openAutoApply = (job: SavedJobRead) => {
    setApplyJob(job);
    setApplyOpen(true);
  };

  const toggleSelect = (id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const loadJobIntoForm = (job: SavedJobRead) => {
    setActiveJobId(job.id);
    setJobForm(jobToForm(job));
    setPackOverride(null);
    setTimeout(() => jobFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  };

  const openInterviewPack = async (job: SavedJobRead) => {
    skipPackClearRef.current = true;
    setActiveJobId(job.id);
    setJobForm(jobToForm(job));
    setTimeout(() => packSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
    if (!job.has_interview_pack) {
      addToast({
        type: "info",
        message: "This job has no saved interview pack yet — click Regenerate pack to create one.",
      });
      return;
    }
    const pack = await jobApi.getInterviewPack(job.id);
    if (pack?.questions?.length) {
      setPackOverride(pack as unknown as Record<string, unknown>);
      qc.setQueryData(["interview-pack", job.id], pack);
    } else {
      addToast({
        type: "info",
        message: "Interview pack data is missing — click Regenerate pack to create a fresh one.",
      });
    }
  };

  const regenerateInterviewPack = (job: SavedJobRead) => {
    skipPackClearRef.current = true;
    setActiveJobId(job.id);
    setJobForm(jobToForm(job));
    generatePackMutation.mutate(job.id);
  };

  useEffect(() => {
    if (skipPackClearRef.current) {
      skipPackClearRef.current = false;
      return;
    }
    setPackOverride(null);
  }, [activeJobId]);

  useEffect(() => {
    const id = searchParamsUrl.get("jobId");
    if (id) setActiveJobId(id);
  }, [searchParamsUrl]);

  const { data: activeJob } = useQuery({
    queryKey: ["job", activeJobId],
    queryFn: () => jobApi.get(activeJobId!),
    enabled: !!activeJobId,
  });

  useEffect(() => {
    if (activeJob) setJobForm(jobToForm(activeJob));
  }, [activeJob?.id]);

  const upsertJob = async (): Promise<string> => {
    const payload = formToSavePayload(jobForm);
    if (activeJobId) {
      const updated = await jobApi.update(activeJobId, payload);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["job", activeJobId] });
      return updated.id;
    }
    const created = await jobApi.save(payload);
    setActiveJobId(created.id);
    qc.invalidateQueries({ queryKey: ["jobs"] });
    return created.id;
  };

  const saveMutation = useMutation({
    mutationFn: upsertJob,
    onSuccess: () => addToast({ type: "success", message: "Job saved." }),
    onError: () => addToast({ type: "error", message: "Could not save job." }),
  });

  const { data: interviewPack, isLoading: packLoading, refetch: refetchPack } = useQuery({
    queryKey: ["interview-pack", activeJobId],
    queryFn: () => jobApi.getInterviewPack(activeJobId!),
    enabled: !!activeJobId,
  });

  const generatePackMutation = useMutation({
    mutationFn: async (jobIdOverride?: string) => {
      const jobId = jobIdOverride ?? await upsertJob();
      skipPackClearRef.current = true;
      setActiveJobId(jobId);
      return jobApi.generateInterviewPack(jobId, { include_study_material: true });
    },
    onSuccess: (pack) => {
      const jobId = pack.job_id ?? activeJobId;
      skipPackClearRef.current = true;
      setPackOverride(pack as unknown as Record<string, unknown>);
      if (jobId) qc.setQueryData(["interview-pack", jobId], pack);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      addToast({
        type: "success",
        title: "Interview pack ready!",
        message: `${pack.questions?.length ?? 0} questions with study guides — scroll down to review.`,
      });
      setTimeout(() => packSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 300);
    },
    onError: (err: ApiError) => {
      addToast({
        type: "error",
        title: "Interview pack failed",
        message: err.message || "Generation failed. Check your Gemini API key in .env or try again.",
      });
    },
  });

  const downloadPackMutation = useMutation({
    mutationFn: async (format: "pdf" | "study_material" | "questions_answers" = "pdf") => {
      if (!activeJobId) throw new Error("no-job");
      const blob = await jobApi.downloadInterviewPackPdf(activeJobId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const suffix = format === "pdf" ? "interview_pack" : format;
      a.download = `${(jobForm.title || "interview_pack").replace(/\s+/g, "_")}_${suffix}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
    onSuccess: () => addToast({ type: "success", message: "PDF downloaded." }),
    onError: () => addToast({ type: "error", message: "PDF download failed. Generate a pack first." }),
  });

  const selectPopularRole = async (role: PopularJobRole) => {
    setSelectingRoleId(role.id);
    try {
      const form = popularRoleToForm(role);
      setJobForm(form);
      const saved = await jobApi.save(savePayloadFromPopularRole(form));
      setActiveJobId(saved.id);
      qc.invalidateQueries({ queryKey: ["jobs"] });
      qc.invalidateQueries({ queryKey: ["job", saved.id] });
      await generatePackMutation.mutateAsync(saved.id);
      setTimeout(() => packSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    } catch {
      addToast({ type: "error", message: "Could not prepare this role. Try again." });
    } finally {
      setSelectingRoleId(null);
    }
  };

  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get() });
  const userSkills = useMemo(
    () => (profile?.skills ?? []).map((s: string | { name?: string }) => (typeof s === "string" ? s : s.name ?? "")),
    [profile]
  );

  const { data: allJobs, isLoading: listLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => jobApi.list(),
  });

  const { data: searchResults } = useQuery({
    queryKey: ["jobs-search", savedFilter],
    queryFn: () => jobApi.searchSaved({ q: savedFilter }),
    enabled: !!savedFilter.trim(),
  });

  const displayedJobs = useMemo(() => {
    if (!savedFilter.trim()) return allJobs ?? [];
    return searchResults ?? (allJobs ?? []).filter((j) => {
      const q = savedFilter.toLowerCase();
      return j.title.toLowerCase().includes(q)
        || (j.company_name ?? "").toLowerCase().includes(q)
        || (j.description_raw ?? "").toLowerCase().includes(q);
    });
  }, [allJobs, searchResults, savedFilter]);

  const displayPack = packOverride ?? (interviewPack as Record<string, unknown> | null | undefined);
  const activeJobHasPack = Boolean(
    (displayPack?.questions as unknown[] | undefined)?.length
    || normalizeInterviewPack(displayPack)?.skill_clusters?.some((c) => c.questions.length > 0),
  );
  const showOpenPackAction = activeJobHasPack;
  const showRegeneratePackAction = Boolean(
    activeJobId
    && !activeJobHasPack
    && (activeJob?.interview_pack_generated_at || displayedJobs.find((j) => j.id === activeJobId)?.interview_pack_generated_at),
  );

  return (
    <div className="feature-page">
      <div className="feature-page__inner">
      <motion.div className="feature-hero" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <span className="feature-hero__eyebrow"><Briefcase size={14} /> Job search & interview prep</span>
        <h1 className="feature-hero__title gradient-text">Jobs & Interview Prep</h1>
        <p className="feature-hero__subtitle">
          Search live jobs on the web, paste a URL, use a posting for interview prep & CV generation — all in one flow.
        </p>
      </motion.div>

      <JobDiscoveryPanel
        onUseJob={(job) => { loadJobIntoForm(job); qc.invalidateQueries({ queryKey: ["jobs"] }); }}
        usingUrl={null}
      />

      <PopularJobRolesPanel
        onSelectRole={selectPopularRole}
        selectingRoleId={selectingRoleId}
      />

      <DefaultCVSelector value={defaultCvId} onChange={setDefaultCvId} />

      <div ref={jobFormRef} style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "1.5rem", marginBottom: "1.5rem" }} className="job-prep-layout">
        <JobDetailsForm
          form={jobForm}
          onChange={setJobForm}
          onSave={() => saveMutation.mutate()}
          onGeneratePack={() => generatePackMutation.mutate(undefined)}
          onViewPack={showOpenPackAction ? () => packSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }) : undefined}
          hasInterviewPack={showOpenPackAction}
          onClear={() => { setActiveJobId(null); setPackOverride(null); }}
          saving={saveMutation.isPending}
          generating={generatePackMutation.isPending}
          activeJobId={activeJobId}
        />
        <div className="feature-glass feature-panel" style={{ alignSelf: "start", maxHeight: 480, overflowY: "auto" }}>
          <h3 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem" }}>Quick actions</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem" }}>
            <Button variant="secondary" size="sm" leftIcon={<FileText size={14} />} disabled={!activeJobId} onClick={() => activeJobId && navigate(`/cv-builder?jobId=${activeJobId}`)}>
              Build CV for this job
            </Button>
            {showOpenPackAction && activeJobId && (
              <Button variant="primary" size="sm" leftIcon={<BookOpen size={14} />} onClick={() => packSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}>
                Open interview pack
              </Button>
            )}
            {showRegeneratePackAction && activeJobId && (
              <Button variant="secondary" size="sm" leftIcon={<Zap size={14} />} onClick={() => generatePackMutation.mutate(activeJobId)}>
                Regenerate pack
              </Button>
            )}
            <Button variant="secondary" size="sm" leftIcon={<Zap size={14} />} disabled={!activeJobId} onClick={() => activeJob && openAutoApply(activeJob)}>
              Auto apply
            </Button>
          </div>
          <h3 style={{ fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.75rem" }}>Recent saved jobs</h3>
          {!displayedJobs.length ? (
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>No saved jobs yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              {displayedJobs.slice(0, 8).map((job) => (
                <button
                  key={job.id}
                  type="button"
                  onClick={() => loadJobIntoForm(job)}
                  style={{
                    textAlign: "left", padding: "0.6rem 0.75rem", borderRadius: "10px", cursor: "pointer",
                    border: activeJobId === job.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                    background: activeJobId === job.id ? "rgba(139,92,246,0.08)" : "transparent",
                  }}
                >
                  <p style={{ fontWeight: 600, fontSize: "0.8rem" }}>{job.title}</p>
                  <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{job.company_name}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div ref={packSectionRef} id="interview-pack-section">
        <InterviewPackView
          pack={displayPack}
          loading={packLoading && !packOverride}
          generating={generatePackMutation.isPending}
          jobTitle={jobForm.title}
          jobId={activeJobId}
          onRegenerate={() => generatePackMutation.mutate(undefined)}
          onDownloadPdf={(fmt) => downloadPackMutation.mutate(fmt ?? "pdf")}
          downloadingPdf={downloadPackMutation.isPending}
        />
      </div>

      <div className="feature-glass feature-panel">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
          <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.1rem" }}>
            Your saved jobs {displayedJobs.length > 0 && `(${displayedJobs.length})`}
          </h2>
          <div style={{ minWidth: 220, flex: 1, maxWidth: 320 }}>
            <Input
              placeholder="Filter saved jobs…"
              value={savedFilter}
              onChange={(e) => setSavedFilter(e.target.value)}
              leftIcon={<Search size={14} />}
              fullWidth
            />
          </div>
          {selectedIds.size > 0 && (
            <Button variant="primary" size="sm" leftIcon={<Zap size={14} />} onClick={() => addToast({ type: "info", message: `Bulk apply queued for ${selectedIds.size} jobs (sequential processing).` })}>
              Auto Apply to Selected ({selectedIds.size})
            </Button>
          )}
        </div>
        {listLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16 }} />)}
          </div>
        ) : !displayedJobs.length ? (
          <div style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
            <Globe size={40} style={{ margin: "0 auto 1rem", opacity: 0.3 }} />
            <p>No saved jobs yet. Search the web above and click <strong>Use this job</strong>.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {displayedJobs.map((job, i) => (
              <motion.div key={job.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}>
                <SavedJobCard
                  job={job}
                  userSkills={userSkills}
                  selected={selectedIds.has(job.id)}
                  onSelect={(c) => toggleSelect(job.id, c)}
                  onAutoApply={() => openAutoApply(job)}
                  onLoad={() => loadJobIntoForm(job)}
                  onViewPack={() => openInterviewPack(job)}
                  onRegeneratePack={() => regenerateInterviewPack(job)}
                  isActive={activeJobId === job.id}
                />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <AutoApplyModal job={applyJob} open={applyOpen} onClose={() => { setApplyOpen(false); setApplyJob(null); }} />
      </div>
    </div>
  );
}
