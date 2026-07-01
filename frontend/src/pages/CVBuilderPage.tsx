/**
 * CVBuilderPage.tsx
 * =================
 * Two-panel CV builder:
 *   Left  — form controls (sections, template picker, target job)
 *   Right — live preview panel with 10 template styles, zoom, ATS/Visual toggle
 *
 * GUARDRAIL: The system NEVER invents data. All content comes strictly from the
 * user's saved profile. The AI "generates" formatting improvements and bullet
 * rewrites only — the underlying experience, company names, dates, and
 * certifications are always sourced from profile data.
 */

import { useState, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText, Download, Eye, Maximize2, Minimize2, Zap,
  ChevronDown, ChevronUp, LayoutTemplate, AlignLeft,
  CheckCircle, Info, Loader2, ZoomIn, ZoomOut, RefreshCw,
  Briefcase, GraduationCap, Award, Code, User, Globe,
} from "lucide-react";
import { cvApi, profileApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { GeneratedCVRead } from "../types/api";

// ─── Constants ─────────────────────────────────────────────────────────────

const TEMPLATES = [
  { id: "modern",      label: "Modern",      accent: "#8B5CF6", category: "visual" },
  { id: "professional",label: "Professional", accent: "#0EA5E9", category: "visual" },
  { id: "minimal",     label: "Minimal",     accent: "#6B7280", category: "ats" },
  { id: "bold",        label: "Bold",        accent: "#F59E0B", category: "visual" },
  { id: "elegant",     label: "Elegant",     accent: "#EC4899", category: "visual" },
  { id: "executive",   label: "Executive",   accent: "#1E40AF", category: "visual" },
  { id: "tech",        label: "Tech",        accent: "#10B981", category: "ats" },
  { id: "creative",    label: "Creative",    accent: "#F97316", category: "visual" },
  { id: "academic",    label: "Academic",    accent: "#7C3AED", category: "ats" },
  { id: "compact",     label: "Compact",     accent: "#374151", category: "ats" },
];

const SECTIONS = [
  { id: "summary",        label: "Summary",         icon: <User size={14} /> },
  { id: "experience",     label: "Experience",       icon: <Briefcase size={14} /> },
  { id: "education",      label: "Education",        icon: <GraduationCap size={14} /> },
  { id: "skills",         label: "Skills",           icon: <Code size={14} /> },
  { id: "certifications", label: "Certifications",   icon: <Award size={14} /> },
  { id: "projects",       label: "Projects",         icon: <Globe size={14} /> },
];

// ─── Mock CV preview renderer ───────────────────────────────────────────────
// In production this would be a real-time PDF preview via a backend endpoint.
// Here we render a styled HTML representation of the CV content.

function CVPreviewContent({
  template,
  mode,
  profile,
  targetJob,
  targetCompany,
  enabledSections,
}: {
  template: (typeof TEMPLATES)[0];
  mode: "visual" | "ats";
  profile: any;
  targetJob: string;
  targetCompany: string;
  enabledSections: string[];
}) {
  const name = (profile as any)?.full_name ?? "Your Name";
  const email = profile?.email ?? "email@example.com";
  const phone = profile?.phone ?? "";
  const location = profile?.location ?? "";
  const summary = profile?.summary ?? "Experienced professional with a strong track record of delivering impactful results.";
  const experience = profile?.experience ?? [];
  const education = profile?.education ?? [];
  const skills = profile?.skills ?? [];
  const certs = profile?.certifications ?? [];
  const projects = profile?.projects ?? [];

  const accent = mode === "ats" ? "#333" : template.accent;
  const fontFamily = mode === "ats"
    ? "'Arial', sans-serif"
    : template.id === "elegant" ? "'Georgia', serif"
    : template.id === "academic" ? "'Times New Roman', serif"
    : "var(--font-sans)";

  const sectionStyle: React.CSSProperties = {
    marginBottom: "1.25rem",
    borderBottom: mode === "ats" ? "1px solid #ccc" : `2px solid ${accent}22`,
    paddingBottom: "0.75rem",
  };
  const sectionHeadStyle: React.CSSProperties = {
    fontFamily,
    fontSize: mode === "ats" ? "0.8rem" : "0.75rem",
    fontWeight: 700,
    color: mode === "ats" ? "#000" : accent,
    textTransform: "uppercase",
    letterSpacing: mode === "ats" ? "0.05em" : "0.1em",
    marginBottom: "0.6rem",
  };

  return (
    <div style={{
      fontFamily,
      fontSize: "0.72rem",
      color: "#1a1a1a",
      background: "#fff",
      padding: "2rem 2.25rem",
      minHeight: "297mm",
      boxSizing: "border-box",
      lineHeight: 1.45,
    }}>
      {/* Header */}
      <div style={{
        marginBottom: "1.5rem",
        paddingBottom: "1rem",
        borderBottom: `3px solid ${mode === "ats" ? "#333" : accent}`,
      }}>
        <h1 style={{ fontFamily, fontSize: "1.4rem", fontWeight: 700, color: mode === "ats" ? "#000" : accent, margin: 0 }}>{name}</h1>
        {targetJob && (
          <p style={{ fontSize: "0.8rem", fontWeight: 500, color: "#555", margin: "3px 0 6px" }}>{targetJob}{targetCompany && ` · Targeting ${targetCompany}`}</p>
        )}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", fontSize: "0.72rem", color: "#555", marginTop: "4px" }}>
          {email    && <span>{email}</span>}
          {phone    && <span>{phone}</span>}
          {location && <span>{location}</span>}
        </div>
      </div>

      {/* Summary */}
      {enabledSections.includes("summary") && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Professional Summary</p>
          <p>{summary}</p>
        </div>
      )}

      {/* Experience */}
      {enabledSections.includes("experience") && experience.length > 0 && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Work Experience</p>
          {experience.map((exp: any, i: number) => (
            <div key={i} style={{ marginBottom: "0.75rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{exp.title ?? "Job Title"}</strong>
                <span style={{ color: "#777" }}>{exp.start_date} – {exp.end_date ?? "Present"}</span>
              </div>
              <div style={{ color: "#555", marginBottom: "4px" }}>{exp.company}</div>
              {exp.bullets?.slice(0, 3).map((b: string, j: number) => (
                <div key={j} style={{ paddingLeft: "0.75rem" }}>• {b}</div>
              ))}
            </div>
          ))}
          {experience.length === 0 && (
            <p style={{ color: "#aaa", fontStyle: "italic" }}>No experience data — add it in your Profile.</p>
          )}
        </div>
      )}

      {/* Education */}
      {enabledSections.includes("education") && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Education</p>
          {education.length > 0 ? education.map((edu: any, i: number) => (
            <div key={i} style={{ marginBottom: "0.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{edu.degree ?? "Degree"}</strong>
                <span style={{ color: "#777" }}>{edu.graduation_year}</span>
              </div>
              <div style={{ color: "#555" }}>{edu.institution}</div>
            </div>
          )) : (
            <p style={{ color: "#aaa", fontStyle: "italic" }}>No education data — add it in your Profile.</p>
          )}
        </div>
      )}

      {/* Skills */}
      {enabledSections.includes("skills") && skills.length > 0 && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Skills</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {skills.map((s: string, i: number) => (
              <span key={i} style={{
                padding: "2px 8px",
                borderRadius: "4px",
                background: mode === "ats" ? "#eee" : `${accent}18`,
                color: mode === "ats" ? "#333" : accent,
                fontSize: "0.68rem",
              }}>{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Certifications */}
      {enabledSections.includes("certifications") && certs.length > 0 && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Certifications</p>
          {certs.map((c: any, i: number) => (
            <div key={i}>• {typeof c === "string" ? c : c.name}</div>
          ))}
        </div>
      )}

      {/* Projects */}
      {enabledSections.includes("projects") && projects.length > 0 && (
        <div style={sectionStyle}>
          <p style={sectionHeadStyle}>Projects</p>
          {projects.slice(0, 3).map((p: any, i: number) => (
            <div key={i} style={{ marginBottom: "0.5rem" }}>
              <strong>{p.name ?? "Project"}</strong>
              {p.description && <div style={{ color: "#555" }}>{p.description}</div>}
            </div>
          ))}
        </div>
      )}

      {/* ATS watermark */}
      {mode === "ats" && (
        <div style={{ marginTop: "2rem", fontSize: "0.65rem", color: "#bbb", textAlign: "center" }}>
          ATS-optimised plain text format — all content sourced from your profile
        </div>
      )}
    </div>
  );
}

// ─── Template picker ───────────────────────────────────────────────────────
function TemplatePicker({ selected, onChange }: { selected: string; onChange: (id: string) => void }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "0.5rem" }}>
      {TEMPLATES.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          style={{
            padding: "0.5rem 0.35rem",
            borderRadius: "8px",
            border: selected === t.id ? `2px solid ${t.accent}` : "1px solid var(--border-subtle)",
            background: selected === t.id ? `${t.accent}14` : "var(--bg-overlay)",
            cursor: "pointer",
            color: selected === t.id ? t.accent : "var(--text-secondary)",
            fontSize: "0.7rem",
            fontWeight: selected === t.id ? 700 : 400,
            transition: "all 0.15s",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
          }}
        >
          <div style={{ width: "20px", height: "4px", borderRadius: "2px", background: t.accent }} />
          {t.label}
          <span style={{ fontSize: "0.6rem", color: "#999" }}>{t.category.toUpperCase()}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Section toggles ───────────────────────────────────────────────────────
function SectionToggles({ enabled, onChange }: { enabled: string[]; onChange: (s: string[]) => void }) {
  const toggle = (id: string) =>
    onChange(enabled.includes(id) ? enabled.filter(x => x !== id) : [...enabled, id]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {SECTIONS.map(s => (
        <label key={s.id} style={{ display: "flex", alignItems: "center", gap: "0.75rem", cursor: "pointer", padding: "0.5rem 0.625rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", background: enabled.includes(s.id) ? "rgba(139,92,246,0.05)" : "transparent" }}>
          <input
            type="checkbox"
            checked={enabled.includes(s.id)}
            onChange={() => toggle(s.id)}
            style={{ accentColor: "var(--accent-violet)", width: "14px", height: "14px" }}
          />
          <span style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", color: "var(--text-primary)" }}>
            {s.icon}{s.label}
          </span>
        </label>
      ))}
    </div>
  );
}

// ─── Saved CVs list ────────────────────────────────────────────────────────
function SavedCVsList({ onLoad }: { onLoad: (cv: GeneratedCVRead) => void }) {
  const { data: cvs, isLoading } = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });
  const qc = useQueryClient();
  const { addToast } = useUIStore();

  const deleteMutation = useMutation({
    mutationFn: (id: string) => cvApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["cvs"] }); addToast({ type: "success", message: "CV deleted." }); },
  });

  if (isLoading) return <Spinner size="sm" />;
  if (!cvs?.length) return <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>No CVs yet. Generate your first below.</p>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
      {cvs.map((cv: GeneratedCVRead) => (
        <div key={cv.id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0.75rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", background: "var(--bg-overlay)" }}>
          <FileText size={14} style={{ color: "var(--accent-violet)", flexShrink: 0 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: "0.8rem", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{cv.name || cv.template || "Untitled CV"}</p>
            <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{cv.template} · {cv.enabled_sections?.length ?? 0} sections</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => onLoad(cv)}>Load</Button>
          <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(cv.id)}>×</Button>
        </div>
      ))}
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────
export default function CVBuilderPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const { data: profile } = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get() });

  // Form state
  const [selectedTemplate, setSelectedTemplate] = useState("modern");
  const [mode, setMode] = useState<"visual" | "ats">("visual");
  const [enabledSections, setEnabledSections] = useState(["summary", "experience", "education", "skills", "certifications"]);
  const [targetJob, setTargetJob] = useState("");
  const [targetCompany, setTargetCompany] = useState("");
  const [cvName, setCvName] = useState("");
  const [zoom, setZoom] = useState(0.65);
  const [lastCvId, setLastCvId] = useState<string | null>(null);

  // Newest CV first — used as the export target when the user hasn't just
  // generated one this session.
  const { data: cvs } = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });

  const template = TEMPLATES.find(t => t.id === selectedTemplate) ?? TEMPLATES[0];

  const generateMutation = useMutation({
    mutationFn: () => cvApi.generate({
      template: selectedTemplate,
      enabled_sections: enabledSections,
      target_job_title: targetJob || undefined,
      target_company: targetCompany || undefined,
      name: cvName || `${(profile as any)?.full_name ?? "My"} CV — ${selectedTemplate}`,
    }),
    onSuccess: (cv: GeneratedCVRead) => {
      setLastCvId(cv.id);
      qc.invalidateQueries({ queryKey: ["cvs"] });
      addToast({ type: "success", title: "CV generated!", message: "Your CV has been saved. Export it below." });
    },
    onError: () => addToast({ type: "error", message: "CV generation failed. Try again." }),
  });

  // Real export: fetch the PDF (or DOCX) blob from the backend export route and
  // trigger a browser download. Replaces the previous placeholder toast (§36 #4).
  const exportMutation = useMutation({
    mutationFn: async (format: "pdf" | "docx") => {
      const cvId = lastCvId ?? cvs?.[0]?.id;
      if (!cvId) throw new Error("no-cv");
      const blob = await cvApi.downloadPdf(cvId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(cvName || "cv").replace(/\s+/g, "_") || "cv"}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
    onError: (e: any) =>
      addToast(
        e?.message === "no-cv"
          ? { type: "info", message: "Generate a CV first, then export." }
          : { type: "error", message: "Export failed. Please try again." }
      ),
  });

  const loadCV = (cv: GeneratedCVRead) => {
    setSelectedTemplate(cv.template || "modern");
    setEnabledSections(cv.enabled_sections ?? []);
    setTargetJob(cv.target_job_title ?? "");
    setTargetCompany(cv.target_company ?? "");
    setCvName(cv.name || "");
    addToast({ type: "info", message: `Loaded: ${cv.name || cv.template}` });
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 56px)", overflow: "hidden" }}>
      {/* ── Left panel ── */}
      <div style={{
        width: "340px", flexShrink: 0,
        overflowY: "auto", padding: "1.5rem",
        borderRight: "1px solid var(--border-subtle)",
        background: "var(--bg-base)",
      }}>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.3rem", fontWeight: 700, marginBottom: "0.25rem" }}>CV Builder</h1>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
          Content is sourced entirely from your profile — AI improves the writing only.
        </p>

        {/* Profile data notice */}
        <div style={{ display: "flex", gap: "0.5rem", padding: "0.6rem 0.75rem", borderRadius: "10px", background: "rgba(6,182,212,0.07)", border: "1px solid rgba(6,182,212,0.2)", marginBottom: "1.5rem", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
          <Info size={13} style={{ color: "var(--accent-cyan)", marginTop: "1px", flexShrink: 0 }} />
          AI never invents experience, companies, dates, or certifications. All data comes from your profile.
        </div>

        {/* CV name */}
        <div style={{ marginBottom: "1.25rem" }}>
          <Input label="CV name (optional)" value={cvName} onChange={e => setCvName(e.target.value)} placeholder="e.g. Senior Engineer — Google" fullWidth />
        </div>

        {/* Target job */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.5rem" }}>
          <Input label="Target job title" value={targetJob} onChange={e => setTargetJob(e.target.value)} placeholder="e.g. Senior Software Engineer" fullWidth />
          <Input label="Target company (optional)" value={targetCompany} onChange={e => setTargetCompany(e.target.value)} placeholder="e.g. Google" fullWidth />
        </div>

        {/* Sections */}
        <div style={{ marginBottom: "1.5rem" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.75rem", color: "var(--text-secondary)" }}>SECTIONS</p>
          <SectionToggles enabled={enabledSections} onChange={setEnabledSections} />
        </div>

        {/* Template picker */}
        <div style={{ marginBottom: "1.5rem" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.75rem", color: "var(--text-secondary)" }}>TEMPLATE</p>
          <TemplatePicker selected={selectedTemplate} onChange={setSelectedTemplate} />
        </div>

        {/* Mode toggle */}
        <div style={{ marginBottom: "1.5rem" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.75rem", color: "var(--text-secondary)" }}>MODE</p>
          <div style={{ display: "flex", borderRadius: "10px", overflow: "hidden", border: "1px solid var(--border-subtle)" }}>
            {(["visual", "ats"] as const).map(m => (
              <button key={m} onClick={() => setMode(m)} style={{
                flex: 1, padding: "0.5rem",
                background: mode === m ? "var(--accent-violet)" : "transparent",
                color: mode === m ? "#fff" : "var(--text-secondary)",
                border: "none", cursor: "pointer", fontSize: "0.8rem", fontWeight: 600,
              }}>
                {m === "visual" ? "🎨 Visual" : "📄 ATS"}
              </button>
            ))}
          </div>
          <p style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
            {mode === "ats" ? "Plain text format optimised for Applicant Tracking Systems." : "Rich design with colours and typography."}
          </p>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
          <Button variant="primary" fullWidth onClick={() => generateMutation.mutate()} loading={generateMutation.isPending} leftIcon={<Zap size={15} />}>
            Generate & Save CV
          </Button>
          <Button variant="secondary" fullWidth leftIcon={<Download size={15} />} loading={exportMutation.isPending} onClick={() => exportMutation.mutate("pdf")}>
            Export PDF
          </Button>
        </div>

        {/* Saved CVs */}
        <div style={{ marginTop: "1.75rem" }}>
          <p style={{ fontSize: "0.8rem", fontWeight: 600, marginBottom: "0.75rem", color: "var(--text-secondary)" }}>SAVED CVs</p>
          <SavedCVsList onLoad={loadCV} />
        </div>
      </div>

      {/* ── Right preview panel ── */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column", background: "#e5e7eb" }}>
        {/* Preview toolbar */}
        <div style={{
          display: "flex", alignItems: "center", gap: "0.75rem",
          padding: "0.625rem 1.25rem",
          background: "var(--bg-glass)", backdropFilter: "blur(16px)",
          borderBottom: "1px solid var(--border-subtle)", flexShrink: 0,
        }}>
          <div style={{ flex: 1, display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Badge color="violet" size="sm" dot>{template.label}</Badge>
            <Badge color={mode === "ats" ? "cyan" : "amber"} size="sm">{mode.toUpperCase()}</Badge>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.max(0.3, z - 0.1))}><ZoomOut size={14} /></Button>
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", minWidth: "36px", textAlign: "center" }}>{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.min(1.2, z + 0.1))}><ZoomIn size={14} /></Button>
            <Button variant="ghost" size="sm" onClick={() => setZoom(0.65)}><RefreshCw size={14} /></Button>
          </div>
        </div>

        {/* Preview scroll area */}
        <div style={{ flex: 1, overflow: "auto", display: "flex", justifyContent: "center", padding: "2rem" }}>
          <motion.div
            animate={{ scale: zoom }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            style={{
              transformOrigin: "top center",
              width: "210mm",
              minWidth: "210mm",
              boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
              borderRadius: "4px",
              overflow: "hidden",
            }}
          >
            <CVPreviewContent
              template={template}
              mode={mode}
              profile={profile}
              targetJob={targetJob}
              targetCompany={targetCompany}
              enabledSections={enabledSections}
            />
          </motion.div>
        </div>

        {/* Page break indicator */}
        <div style={{
          position: "absolute", bottom: "120px", left: "50%", transform: "translateX(-50%)",
          display: "flex", alignItems: "center", gap: "0.5rem",
          padding: "3px 10px", borderRadius: "999px",
          background: "rgba(0,0,0,0.5)", color: "#fff", fontSize: "0.65rem",
          pointerEvents: "none",
        }}>
          ── Page break ──
        </div>
      </div>
    </div>
  );
}
