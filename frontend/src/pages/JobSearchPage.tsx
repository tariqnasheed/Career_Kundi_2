/**
 * JobSearchPage.tsx
 * ==================
 * Full job search hub:
 *  - Prominent URL paste bar at the top
 *  - Extraction progress + editable field form when incomplete
 *  - Extracted job preview card with instant actions
 *  - Saved jobs list
 *  - Auto Apply modal with full safety workflow
 */

import { useState, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Link2, Loader2, BookOpen, FileText, Bookmark, Zap,
  CheckCircle, AlertCircle, X, Send, ArrowRight,
  MapPin, Building, DollarSign, Clock, ExternalLink,
  ChevronDown, ChevronUp, Eye,
} from "lucide-react";
import { applyApi, jobApi, cvApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Modal, ModalBody, ModalFooter } from "../components/ui/Modal";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { SavedJobRead, GeneratedCVRead } from "../types/api";

// ─── URL Import bar ────────────────────────────────────────────────────────
function UrlImportBar({ onExtracted }: { onExtracted: (data: any) => void }) {
  const [url, setUrl] = useState("");
  const { addToast } = useUIStore();

  const extractMutation = useMutation({
    mutationFn: (u: string) => applyApi.extractUrl(u),
    onSuccess: (data: any) => {
      onExtracted(data);
      if (data.guardrail_passed === false && data.blocked_domain) {
        addToast({ type: "warning", title: "Platform blocked", message: "This domain blocks scraping. Fill in the details manually below." });
      } else if (data.extraction_incomplete) {
        addToast({ type: "info", message: "Partial extraction — fill in the missing fields." });
      } else {
        addToast({ type: "success", message: "Job imported successfully!" });
      }
    },
    onError: () => addToast({ type: "error", message: "Could not extract job from URL. Check the URL and try again." }),
  });

  const handleImport = () => {
    if (!url.trim()) return;
    extractMutation.mutate(url.trim());
  };

  return (
    <div style={{
      padding: "1.5rem 2rem", background: "var(--gradient-primary-soft)",
      borderRadius: "20px", border: "1px solid var(--border-default)",
      marginBottom: "2rem",
    }}>
      <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.25rem", marginBottom: "0.5rem" }}>
        Import a job from any URL
      </h2>
      <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1rem" }}>
        Paste a link to any job posting and AI will extract all the details automatically.
      </p>
      <div style={{ display: "flex", gap: "0.75rem" }}>
        <div style={{ flex: 1 }}>
          <Input
            type="url"
            placeholder="https://company.com/jobs/senior-engineer..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            leftIcon={<Link2 size={15} />}
            fullWidth
            onKeyDown={e => { if (e.key === "Enter") handleImport(); }}
          />
        </div>
        <Button
          variant="primary"
          onClick={handleImport}
          loading={extractMutation.isPending}
          disabled={!url.trim()}
        >
          Import Job
        </Button>
      </div>
    </div>
  );
}

// ─── Editable field form (when extraction is incomplete) ──────────────────
function ExtractedJobForm({ data, onSave }: { data: any; onSave: (fields: any) => void }) {
  const f = data.extracted_fields ?? {};
  const [fields, setFields] = useState({
    title: f.title ?? "",
    company_name: f.company_name ?? "",
    location: f.location ?? "",
    employment_type: f.employment_type ?? "",
    description_raw: f.description_raw ?? "",
    salary_min: f.salary_min ?? "",
    salary_max: f.salary_max ?? "",
  });

  const set = (k: string) => (e: any) => setFields(p => ({ ...p, [k]: e.target.value }));

  return (
    <Card padding="lg" style={{ marginBottom: "1.5rem" }}>
      <CardHeader>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <AlertCircle size={18} style={{ color: "var(--accent-amber)" }} />
          <CardTitle>Review extracted data</CardTitle>
        </div>
        {data.missing_fields?.length > 0 && (
          <Badge color="amber" size="sm">
            {data.missing_fields.length} field{data.missing_fields.length > 1 ? "s" : ""} missing
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
          We couldn't extract everything from the page. Fill in any missing fields below before importing.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
          <Input label="Job title *" value={fields.title} onChange={set("title")} fullWidth error={!fields.title ? "Required" : undefined} />
          <Input label="Company name *" value={fields.company_name} onChange={set("company_name")} fullWidth error={!fields.company_name ? "Required" : undefined} />
          <Input label="Location" value={fields.location} onChange={set("location")} fullWidth />
          <Input label="Employment type" value={fields.employment_type} onChange={set("employment_type")} fullWidth />
          <Input label="Salary min (£)" type="number" value={fields.salary_min} onChange={set("salary_min")} fullWidth />
          <Input label="Salary max (£)" type="number" value={fields.salary_max} onChange={set("salary_max")} fullWidth />
        </div>
        <div style={{ marginTop: "1rem" }}>
          <Textarea label="Job description" value={fields.description_raw} onChange={set("description_raw")} fullWidth rows={5} />
        </div>
        <div style={{ marginTop: "1.25rem", display: "flex", justifyContent: "flex-end" }}>
          <Button variant="primary" onClick={() => onSave(fields)} disabled={!fields.title || !fields.company_name}>
            Save & continue
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ─── Instant action buttons ────────────────────────────────────────────────
function InstantActions({ job, onAutoApply }: { job: any; onAutoApply: () => void }) {
  const { addToast } = useUIStore();
  const qc = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: () => jobApi.save(job),
    onSuccess: () => { addToast({ type: "success", message: "Job saved!" }); qc.invalidateQueries({ queryKey: ["jobs"] }); },
  });

  const ACTIONS = [
    {
      label: "Generate Interview Pack",
      icon: <BookOpen size={16} />,
      color: "#8B5CF6",
      onClick: () => addToast({ type: "ai", message: "Starting interview pack generation…" }),
    },
    {
      label: "Build CV for This Job",
      icon: <FileText size={16} />,
      color: "#06B6D4",
      onClick: () => addToast({ type: "ai", message: "Tailoring CV for this role…" }),
    },
    {
      label: "Save Job",
      icon: <Bookmark size={16} />,
      color: "#10B981",
      onClick: () => saveMutation.mutate(),
    },
    {
      label: "Auto Apply",
      icon: <Zap size={16} />,
      color: "#F59E0B",
      onClick: onAutoApply,
    },
  ];

  return (
    <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "1rem" }}>
      {ACTIONS.map(a => (
        <Button
          key={a.label}
          variant="secondary"
          size="sm"
          leftIcon={a.icon}
          onClick={a.onClick}
          style={{ borderColor: `${a.color}44`, color: a.color }}
        >
          {a.label}
        </Button>
      ))}
    </div>
  );
}

// ─── Extracted job preview ─────────────────────────────────────────────────
function ExtractedJobPreview({ fields, onAutoApply }: { fields: any; onAutoApply: () => void }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <Card padding="lg" style={{ marginBottom: "1.5rem", borderColor: "var(--border-default)" }} glow>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
        <div>
          <h3 style={{ fontFamily: "var(--font-heading)", fontSize: "1.2rem", fontWeight: 700, marginBottom: "0.35rem" }}>
            {fields.title}
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            {fields.company_name && <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><Building size={13} />{fields.company_name}</span>}
            {fields.location      && <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><MapPin size={13} />{fields.location}</span>}
            {fields.employment_type && <span style={{ display: "flex", alignItems: "center", gap: "4px" }}><Clock size={13} />{fields.employment_type}</span>}
            {(fields.salary_min || fields.salary_max) && (
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <DollarSign size={13} />
                {fields.salary_min && `£${Number(fields.salary_min).toLocaleString()}`}
                {fields.salary_min && fields.salary_max && " – "}
                {fields.salary_max && `£${Number(fields.salary_max).toLocaleString()}`}
              </span>
            )}
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          {fields.is_remote && <Badge color="emerald" size="sm">Remote</Badge>}
          <Badge color="violet" size="sm" dot>Imported</Badge>
        </div>
      </div>

      {fields.description_raw && (
        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.65 }}>
            {expanded ? fields.description_raw : fields.description_raw.slice(0, 280) + (fields.description_raw.length > 280 ? "…" : "")}
          </p>
          {fields.description_raw.length > 280 && (
            <button
              onClick={() => setExpanded(!expanded)}
              style={{ background: "none", border: "none", color: "var(--accent-violet-bright)", fontSize: "0.8rem", cursor: "pointer", marginTop: "0.5rem", display: "flex", alignItems: "center", gap: "4px" }}
            >
              {expanded ? <><ChevronUp size={13} /> Show less</> : <><ChevronDown size={13} /> Read more</>}
            </button>
          )}
        </div>
      )}

      {fields.requirements?.length > 0 && (
        <div style={{ marginTop: "1rem" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Requirements</p>
          <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {fields.requirements.slice(0, 5).map((r: string, i: number) => (
              <li key={i} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "3px" }}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <InstantActions job={fields} onAutoApply={onAutoApply} />
    </Card>
  );
}

// ─── Auto Apply Modal ─────────────────────────────────────────────────────
function AutoApplyModal({ job, open, onClose }: { job: any; open: boolean; onClose: () => void }) {
  const { addToast } = useUIStore();
  const { data: cvs } = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });

  const [step, setStep] = useState<"select" | "review" | "submitting" | "done" | "blocked">("select");
  const [selectedCvId, setSelectedCvId] = useState<string>("");
  const [coverLetterRequested, setCoverLetterRequested] = useState(false);
  const [applicationId, setApplicationId] = useState<string>("");
  const [result, setResult] = useState<any>(null);

  const startMutation = useMutation({
    mutationFn: () => applyApi.startApply(job?.id || "temp", {
      cv_id: selectedCvId || undefined,
      cover_letter_requested: coverLetterRequested,
    }),
    onSuccess: (data: any) => {
      setApplicationId(data.id);
      setStep("review");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () => applyApi.confirm(applicationId),
    onSuccess: (data: any) => {
      setResult(data);
      setStep(data.status === "submitted" ? "done" : data.status === "blocked" ? "blocked" : "done");
      if (data.newly_earned_badges?.length > 0) {
        addToast({ type: "success", title: "Badge earned!", message: `You earned: ${data.newly_earned_badges.join(", ")}` });
      }
    },
    onError: () => {
      addToast({ type: "error", message: "Application failed. Please use the manual link." });
      setStep("blocked");
    },
  });

  const reset = () => {
    setStep("select");
    setSelectedCvId("");
    setCoverLetterRequested(false);
    setApplicationId("");
    setResult(null);
    onClose();
  };

  return (
    <Modal open={open} onClose={reset} title="Auto Apply" size="md">
      <ModalBody>
        {step === "select" && (
          <div>
            <div style={{ padding: "0.75rem", borderRadius: "10px", background: "rgba(139,92,246,0.08)", border: "1px solid var(--border-subtle)", marginBottom: "1.25rem" }}>
              <p style={{ fontWeight: 600, fontSize: "0.875rem" }}>{job?.title}</p>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{job?.company_name}</p>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                Select CV to attach
              </label>
              <select
                value={selectedCvId}
                onChange={e => setSelectedCvId(e.target.value)}
                style={{
                  width: "100%", padding: "0.625rem 0.875rem",
                  background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)",
                  borderRadius: "10px", color: "var(--text-primary)", fontSize: "0.875rem",
                }}
              >
                <option value="">Use profile data (no CV file)</option>
                {cvs?.map((cv: GeneratedCVRead) => (
                  <option key={cv.id} value={cv.id}>{cv.name || cv.template || "Untitled CV"}</option>
                ))}
              </select>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer", padding: "0.75rem", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
              <input
                type="checkbox"
                checked={coverLetterRequested}
                onChange={e => setCoverLetterRequested(e.target.checked)}
                style={{ width: "16px", height: "16px", accentColor: "var(--accent-violet)" }}
              />
              <div>
                <p style={{ fontWeight: 600, fontSize: "0.875rem" }}>Generate a cover letter</p>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>AI will write a tailored cover letter using your profile and this job description. You'll review it before submitting.</p>
              </div>
            </label>

            <div style={{ marginTop: "1.25rem", padding: "0.75rem", borderRadius: "10px", background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.2)" }}>
              <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                <strong>Safety:</strong> We will show you exactly what will be submitted before sending anything. You'll confirm in the next step. We never store passwords or apply without your explicit action.
              </p>
            </div>
          </div>
        )}

        {step === "review" && (
          <div>
            <div style={{ padding: "1rem", borderRadius: "10px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)", marginBottom: "1.25rem" }}>
              <p style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.5rem", color: "var(--text-secondary)" }}>WHAT WILL BE SUBMITTED</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem" }}>
                  <CheckCircle size={13} style={{ color: "var(--accent-emerald)" }} /> Your name and email from your profile
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem" }}>
                  <CheckCircle size={13} style={{ color: "var(--accent-emerald)" }} /> {selectedCvId ? "Selected CV file" : "Profile-based CV data"}
                </div>
                {coverLetterRequested && (
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem" }}>
                    <CheckCircle size={13} style={{ color: "var(--accent-emerald)" }} /> AI-generated cover letter
                  </div>
                )}
              </div>
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.65 }}>
              By confirming, you're authorising CareerKundi to submit this application on your behalf.
              You can always apply manually using the direct link if automation is blocked.
            </p>
          </div>
        )}

        {step === "submitting" && (
          <div style={{ textAlign: "center", padding: "2rem 0" }}>
            <Spinner size="lg" />
            <p style={{ marginTop: "1rem", color: "var(--text-secondary)" }}>Submitting your application…</p>
          </div>
        )}

        {step === "done" && result && (
          <div style={{ textAlign: "center", padding: "1rem 0" }}>
            <div style={{ width: "56px", height: "56px", borderRadius: "50%", background: "rgba(16,185,129,0.12)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1rem" }}>
              <CheckCircle size={28} style={{ color: "var(--accent-emerald)" }} />
            </div>
            <h3 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, marginBottom: "0.5rem" }}>Application submitted!</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1rem" }}>{result.status_detail}</p>
            {result.platform_confirmation && (
              <Badge color="emerald">Confirmation: {result.platform_confirmation}</Badge>
            )}
          </div>
        )}

        {step === "blocked" && (
          <div style={{ textAlign: "center", padding: "1rem 0" }}>
            <div style={{ width: "56px", height: "56px", borderRadius: "50%", background: "rgba(244,63,94,0.1)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 1rem" }}>
              <AlertCircle size={28} style={{ color: "var(--accent-rose)" }} />
            </div>
            <h3 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, marginBottom: "0.5rem" }}>Auto-apply blocked</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginBottom: "1.25rem" }}>
              This platform doesn't allow automated applications. Apply manually using the link below — your CV and cover letter are ready.
            </p>
            {(result?.manual_apply_url || job?.source_url) && (
              <a href={result?.manual_apply_url || job?.source_url} target="_blank" rel="noopener noreferrer">
                <Button variant="primary" rightIcon={<ExternalLink size={14} />}>Apply manually</Button>
              </a>
            )}
          </div>
        )}
      </ModalBody>
      <ModalFooter>
        {step === "select" && (
          <>
            <Button variant="ghost" onClick={reset}>Cancel</Button>
            <Button variant="primary" onClick={() => startMutation.mutate()} loading={startMutation.isPending}>
              Review & Continue
            </Button>
          </>
        )}
        {step === "review" && (
          <>
            <Button variant="ghost" onClick={() => setStep("select")}>Back</Button>
            <Button variant="primary" onClick={() => { setStep("submitting"); confirmMutation.mutate(); }} loading={confirmMutation.isPending}>
              Confirm & Submit
            </Button>
          </>
        )}
        {(step === "done" || step === "blocked") && (
          <Button variant="primary" onClick={reset}>Done</Button>
        )}
      </ModalFooter>
    </Modal>
  );
}

// ─── Saved jobs list ──────────────────────────────────────────────────────
function SavedJobsList() {
  const { data: jobs, isLoading } = useQuery({ queryKey: ["jobs"], queryFn: () => jobApi.list() });

  if (isLoading) return <div style={{ textAlign: "center", padding: "2rem" }}><Spinner /></div>;
  if (!jobs?.length) return (
    <div style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
      <p>No saved jobs yet. Import one using the URL bar above.</p>
    </div>
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {jobs.map((job: any) => (
        <motion.div
          key={job.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            display: "flex", alignItems: "center", gap: "1rem", padding: "1rem 1.25rem",
            borderRadius: "14px", background: "var(--bg-glass)", backdropFilter: "blur(16px)",
            border: "1px solid var(--border-subtle)",
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontWeight: 600, marginBottom: "2px" }}>{job.title}</p>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              {job.company_name} {job.location && `· ${job.location}`}
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexShrink: 0 }}>
            {job.match_score != null && (
              <Badge color={job.match_score >= 80 ? "emerald" : job.match_score >= 60 ? "amber" : "default"} size="sm">
                {Math.round(job.match_score)}%
              </Badge>
            )}
            {job.interview_pack?.length > 0 && <Badge color="violet" size="sm">Pack ready</Badge>}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────
export default function JobSearchPage() {
  const [extractedData, setExtractedData] = useState<any>(null);
  const [editedFields, setEditedFields]   = useState<any>(null);
  const [applyOpen, setApplyOpen]         = useState(false);

  const displayFields = editedFields ?? extractedData?.extracted_fields;

  return (
    <div style={{ padding: "2rem", maxWidth: "900px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.35rem" }}>Job Search</h1>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>Import any job posting and get instant AI-powered career support.</p>
      </motion.div>

      <UrlImportBar onExtracted={(data) => { setExtractedData(data); setEditedFields(null); }} />

      <AnimatePresence>
        {extractedData && (
          <motion.div key="extracted" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {extractedData.extraction_incomplete
              ? <ExtractedJobForm data={extractedData} onSave={setEditedFields} />
              : displayFields && (
                  <ExtractedJobPreview
                    fields={displayFields}
                    onAutoApply={() => setApplyOpen(true)}
                  />
                )
            }
            {editedFields && (
              <ExtractedJobPreview fields={editedFields} onAutoApply={() => setApplyOpen(true)} />
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <Card padding="lg">
        <CardHeader><CardTitle>Saved jobs</CardTitle></CardHeader>
        <CardContent><SavedJobsList /></CardContent>
      </Card>

      <AutoApplyModal
        job={displayFields}
        open={applyOpen}
        onClose={() => setApplyOpen(false)}
      />
    </div>
  );
}
