/**
 * Editable job posting form — populated via web discovery, saved jobs, or manual entry.
 */

import { Save, BookOpen } from "lucide-react";
import { Button } from "../ui/Button";
import { Input, Textarea } from "../ui/Input";
import type { JobFormState } from "../../lib/jobForm";
import { EMPTY_JOB_FORM } from "../../lib/jobForm";

interface JobDetailsFormProps {
  form: JobFormState;
  onChange: (form: JobFormState) => void;
  onSave: () => void;
  onGeneratePack: () => void;
  onViewPack?: () => void;
  hasInterviewPack?: boolean;
  onClear?: () => void;
  saving?: boolean;
  generating?: boolean;
  activeJobId?: string | null;
}

export function JobDetailsForm({
  form, onChange, onSave, onGeneratePack, onViewPack, hasInterviewPack, onClear, saving, generating, activeJobId,
}: JobDetailsFormProps) {
  const set = (patch: Partial<JobFormState>) => onChange({ ...form, ...patch });

  return (
    <div className="feature-glass feature-panel">
      <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.1rem", marginBottom: "0.35rem" }}>
        Job details
      </h2>
      <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1.25rem" }}>
        Auto-filled when you pick a <strong>popular role</strong>, click <strong>Use this job</strong>, or load a saved job — then generate your interview pack or CV.
      </p>

      <div className="feature-grid-2" style={{ marginBottom: "1rem" }}>
        <Input label="Job title *" value={form.title} onChange={(e) => set({ title: e.target.value })} placeholder="Senior Backend Engineer" fullWidth />
        <Input label="Company" value={form.company_name} onChange={(e) => set({ company_name: e.target.value })} placeholder="Acme Corp" fullWidth />
        <Input label="Location" value={form.location} onChange={(e) => set({ location: e.target.value })} placeholder="London / Remote" fullWidth />
        <Input label="Employment type" value={form.employment_type} onChange={(e) => set({ employment_type: e.target.value })} placeholder="Full-time, Contract…" fullWidth />
        <div>
          <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "0.4rem" }}>Experience level</label>
          <select
            value={form.experience_level}
            onChange={(e) => set({ experience_level: e.target.value })}
            style={{ width: "100%", padding: "0.55rem", borderRadius: "8px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", fontSize: "0.8rem" }}
          >
            <option value="">Not specified</option>
            <option value="Entry level (0–2 years)">Entry level (0–2 years)</option>
            <option value="Mid level (3–5 years)">Mid level (3–5 years)</option>
            <option value="Senior (5–8 years)">Senior (5–8 years)</option>
            <option value="Lead / Principal (8+ years)">Lead / Principal (8+ years)</option>
          </select>
        </div>
        <Input label="Company URL" value={form.company_url} onChange={(e) => set({ company_url: e.target.value })} placeholder="https://company.com" fullWidth />
        <Input label="Source URL" value={form.source_url} onChange={(e) => set({ source_url: e.target.value })} placeholder="Original job posting link" fullWidth />
        <Input label="Min salary" type="number" value={form.salary_min} onChange={(e) => set({ salary_min: e.target.value })} placeholder="60000" fullWidth />
        <Input label="Max salary" type="number" value={form.salary_max} onChange={(e) => set({ salary_max: e.target.value })} placeholder="90000" fullWidth />
        <Input label="Currency" value={form.salary_currency} onChange={(e) => set({ salary_currency: e.target.value })} placeholder="GBP" fullWidth />
      </div>

      <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem", fontSize: "0.8rem", cursor: "pointer" }}>
        <input type="checkbox" checked={form.is_remote} onChange={(e) => set({ is_remote: e.target.checked })} style={{ accentColor: "var(--accent-violet)" }} />
        Remote position
      </label>

      <Textarea label="Job description" value={form.description_raw} onChange={(e) => set({ description_raw: e.target.value })} placeholder="Full job description…" rows={6} fullWidth />
      <div style={{ marginTop: "1rem" }}>
        <Textarea label="Responsibilities (one per line)" value={form.responsibilities} onChange={(e) => set({ responsibilities: e.target.value })} rows={4} fullWidth />
      </div>
      <div style={{ marginTop: "1rem" }}>
        <Textarea label="Requirements & qualifications (one per line)" value={form.requirements} onChange={(e) => set({ requirements: e.target.value })} rows={4} fullWidth />
      </div>
      <div style={{ marginTop: "1rem" }}>
        <Textarea label="Benefits (one per line)" value={form.benefits} onChange={(e) => set({ benefits: e.target.value })} rows={3} fullWidth />
      </div>
      <div style={{ marginTop: "1rem" }}>
        <Input label="Required skills (comma-separated)" value={form.skills} onChange={(e) => set({ skills: e.target.value })} placeholder="Python, AWS, PostgreSQL" fullWidth />
      </div>

      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", marginTop: "1.5rem", paddingTop: "1.25rem", borderTop: "1px solid var(--border-subtle)" }}>
        <Button variant="secondary" leftIcon={<Save size={15} />} onClick={onSave} loading={saving} disabled={!form.title.trim()}>
          {activeJobId ? "Update & save" : "Save job"}
        </Button>
        <Button variant="primary" leftIcon={<BookOpen size={15} />} onClick={onGeneratePack} loading={generating} disabled={!form.title.trim()}>
          Generate interview pack
        </Button>
        {hasInterviewPack && onViewPack && (
          <Button variant="secondary" leftIcon={<BookOpen size={15} />} onClick={onViewPack}>
            Open interview pack
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={() => { onChange(EMPTY_JOB_FORM); onClear?.(); }}>Clear form</Button>
      </div>
    </div>
  );
}
