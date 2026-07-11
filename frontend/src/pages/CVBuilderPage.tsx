/**
 * CVBuilderPage.tsx
 * CV Builder MVP shell — profile-driven preview, section toggles, template
 * accents, generate/export actions. Template/PDF/save polish continue in later slices.
 */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText, Zap, ChevronUp, ChevronDown,
  Info, ZoomIn, ZoomOut, RefreshCw,
  Monitor, Smartphone, Printer, Star, GripVertical, User, Sparkles,
} from "lucide-react";
import { cvApi, jobApi, profileApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Badge } from "../components/ui/Badge";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { ApiError, GeneratedCVRead, SavedJobRead } from "../types/api";

function queryErrorMessage(err: unknown): string {
  const msg = (err as ApiError | undefined)?.message;
  return (msg && String(msg).trim()) || "We couldn't load this section. Please try again.";
}

const DEFAULT_CV_KEY = "ck_default_cv_id";

const TEMPLATES = [
  { id: "modern", label: "Modern", accent: "#8B5CF6", category: "visual", backend: "modern" },
  { id: "professional", label: "Classic", accent: "#0EA5E9", category: "visual", backend: "classic" },
  { id: "minimal", label: "Minimalist", accent: "#6B7280", category: "ats", backend: "compact" },
  { id: "bold", label: "Creative", accent: "#F97316", category: "visual", backend: "creative" },
  { id: "elegant", label: "Designer", accent: "#EC4899", category: "visual", backend: "creative" },
  { id: "executive", label: "Executive", accent: "#1E40AF", category: "visual", backend: "classic" },
  { id: "tech", label: "Tech", accent: "#10B981", category: "ats", backend: "modern" },
  { id: "academic", label: "Academic", accent: "#7C3AED", category: "ats", backend: "classic" },
  { id: "compact", label: "ATS-Optimized", accent: "#374151", category: "ats", backend: "compact" },
  { id: "startup", label: "Startup", accent: "#06B6D4", category: "visual", backend: "modern" },
  { id: "federal", label: "Federal / Govt", accent: "#1D4ED8", category: "ats", backend: "classic" },
  { id: "two-column", label: "Two-Column", accent: "#A855F7", category: "visual", backend: "creative" },
];

const BASE_SECTIONS = [
  { id: "summary", label: "Summary" },
  { id: "experience", label: "Experience" },
  { id: "education", label: "Education" },
  { id: "skills", label: "Skills" },
  { id: "projects", label: "Projects" },
  { id: "certifications", label: "Certifications" },
  { id: "publications", label: "Publications" },
  { id: "languages", label: "Languages" },
  { id: "volunteer", label: "Volunteer" },
  { id: "awards", label: "Awards" },
  { id: "references", label: "References" },
  { id: "custom", label: "Custom sections" },
];

type CvSection = { section_id?: string; title: string; content?: string; items?: string[]; entries?: Record<string, unknown>[]; section_type?: string; free_text_content?: string | null; tags?: string[] };

function formatDateRange(start?: string | null, end?: string | null, isCurrent?: boolean) {
  const fmt = (v?: string | null) => (v ? String(v).slice(0, 7) : "");
  if (!start && !end) return "";
  return `${fmt(start)} – ${isCurrent ? "Present" : fmt(end)}`.trim();
}

function CVSectionBlock({ section, accent }: { section: CvSection; accent: string }) {
  const titleStyle = { fontSize: "0.75rem", fontWeight: 700 as const, color: accent, textTransform: "uppercase" as const, letterSpacing: "0.08em", marginBottom: "0.5rem" };

  if (section.content) {
    return (
      <div style={{ marginBottom: "1.25rem" }}>
        <p style={titleStyle}>{section.title}</p>
        <p>{section.content}</p>
      </div>
    );
  }

  if (section.items?.length) {
    return (
      <div style={{ marginBottom: "1.25rem" }}>
        <p style={titleStyle}>{section.title}</p>
        <p>{section.items.join(" · ")}</p>
      </div>
    );
  }

  if (section.free_text_content) {
    return (
      <div style={{ marginBottom: "1.25rem" }}>
        <p style={titleStyle}>{section.title}</p>
        <p>{section.free_text_content}</p>
      </div>
    );
  }

  if (section.tags?.length) {
    return (
      <div style={{ marginBottom: "1.25rem" }}>
        <p style={titleStyle}>{section.title}</p>
        <p>{section.tags.join(" · ")}</p>
      </div>
    );
  }

  if (!section.entries?.length) return null;

  return (
    <div style={{ marginBottom: "1.25rem", borderBottom: `1px solid ${accent}22`, paddingBottom: "0.75rem" }}>
      <p style={titleStyle}>{section.title}</p>
      {section.entries.map((entry, j) => {
        const heading = (entry.job_title || entry.title || entry.name || entry.role || entry.degree) as string | undefined;
        const sub = (entry.company_name || entry.institution || entry.issuing_organization || entry.organization || entry.publisher || entry.field_of_study || entry.proficiency) as string | undefined;
        const dates = formatDateRange(entry.start_date as string, entry.end_date as string, entry.is_current as boolean);
        const bullets = (entry.bullets || entry.description_bullets || entry.key_achievements) as string[] | undefined;
        const description = entry.description != null ? String(entry.description) : "";
        return (
          <div key={j} style={{ marginBottom: "0.6rem" }}>
            {heading && <strong>{heading}</strong>}
            {sub && <span style={{ color: "#555" }}> — {sub}</span>}
            {dates && <div style={{ color: "#777", fontSize: "0.68rem" }}>{dates}</div>}
            {description && <p>{description}</p>}
            {bullets?.map((b, k) => <div key={k} style={{ paddingLeft: "0.75rem" }}>• {b}</div>)}
          </div>
        );
      })}
    </div>
  );
}

function buildProfileSections(profile: any, enabledSections: string[]): CvSection[] {
  if (!profile) return [];
  const sections: CvSection[] = [];

  if (enabledSections.includes("summary") && (profile.bio_summary || profile.professional_headline)) {
    sections.push({ section_id: "summary", title: "Professional Summary", content: profile.bio_summary || profile.professional_headline });
  }
  if (enabledSections.includes("experience") && profile.work_experiences?.length) {
    sections.push({
      section_id: "experience", title: "Work Experience",
      entries: profile.work_experiences.map((we: any) => ({
        job_title: we.job_title, company_name: we.company_name, location: we.location,
        start_date: we.start_date, end_date: we.end_date, is_current: we.is_current,
        bullets: we.description_bullets,
      })),
    });
  }
  if (enabledSections.includes("education") && profile.educations?.length) {
    sections.push({
      section_id: "education", title: "Education",
      entries: profile.educations.map((edu: any) => ({
        degree: edu.degree, institution: edu.institution, field_of_study: edu.field_of_study,
        start_date: edu.start_date, end_date: edu.end_date, is_current: edu.is_current, grade: edu.grade,
      })),
    });
  }
  if (enabledSections.includes("skills") && profile.skills?.length) {
    sections.push({ section_id: "skills", title: "Skills", items: profile.skills.map((s: any) => s.name || s) });
  }
  if (enabledSections.includes("projects") && profile.projects?.length) {
    sections.push({
      section_id: "projects", title: "Projects",
      entries: profile.projects.map((p: any) => ({
        title: p.title, role: p.role, description: p.description, technologies: p.technologies,
        bullets: p.key_achievements,
      })),
    });
  }
  if (enabledSections.includes("certifications") && profile.certifications?.length) {
    sections.push({ section_id: "certifications", title: "Certifications", entries: profile.certifications });
  }
  if (enabledSections.includes("publications") && profile.publications?.length) {
    sections.push({ section_id: "publications", title: "Publications", entries: profile.publications });
  }
  if (enabledSections.includes("languages") && profile.languages?.length) {
    sections.push({ section_id: "languages", title: "Languages", entries: profile.languages });
  }
  if (enabledSections.includes("volunteer") && profile.volunteer_entries?.length) {
    sections.push({ section_id: "volunteer", title: "Volunteer Experience", entries: profile.volunteer_entries });
  }
  if (enabledSections.includes("awards") && profile.awards?.length) {
    sections.push({ section_id: "awards", title: "Awards", entries: profile.awards });
  }
  if (enabledSections.includes("references") && profile.references?.length) {
    sections.push({ section_id: "references", title: "References", entries: profile.references });
  }
  if (enabledSections.includes("custom") && profile.custom_sections?.length) {
    for (const cs of profile.custom_sections) {
      sections.push({
        section_id: `custom-${cs.id}`, title: cs.title, section_type: cs.section_type,
        free_text_content: cs.free_text_content, tags: cs.tags, entries: cs.entries,
      });
    }
  }
  return sections;
}

type PreviewMode = "visual" | "ats";
type ViewportMode = "desktop" | "mobile" | "print";

function RenderedCVPreview({
  content,
  template,
  mode,
}: {
  content: Record<string, unknown>;
  template: (typeof TEMPLATES)[0];
  mode: PreviewMode;
}) {
  const info = (content.personal_info ?? {}) as Record<string, string>;
  const sections = (content.sections ?? []) as CvSection[];
  const accent = mode === "ats" ? "#333" : template.accent;
  const fontFamily = mode === "ats" ? "Arial, sans-serif" : "Georgia, serif";

  return (
    <div style={{ fontFamily, fontSize: "0.72rem", color: "#1a1a1a", background: "#fff", padding: "1.5rem 1.75rem", minHeight: "260mm", lineHeight: 1.45 }}>
      <div style={{ marginBottom: "1.25rem", paddingBottom: "0.75rem", borderBottom: `3px solid ${accent}` }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: accent, margin: 0 }}>{info.full_name ?? "Your Name"}</h1>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", fontSize: "0.68rem", color: "#555", marginTop: "4px" }}>
          {info.email && <span>{info.email}</span>}
          {info.phone && <span>{info.phone}</span>}
          {info.location && <span>{info.location}</span>}
        </div>
        {info.headline && <p style={{ marginTop: "4px", color: "#555", fontSize: "0.7rem" }}>{info.headline}</p>}
      </div>
      {sections.map((section, i) => (
        <CVSectionBlock key={section.section_id ?? i} section={section} accent={accent} />
      ))}
    </div>
  );
}

function ProfileCVPreview({
  template, mode, profile, targetJob, targetCompany, enabledSections, roleTargeted, targetRoleTitle,
}: {
  template: (typeof TEMPLATES)[0];
  mode: PreviewMode;
  profile: any;
  targetJob: string;
  targetCompany: string;
  enabledSections: string[];
  roleTargeted?: boolean;
  targetRoleTitle?: string;
}) {
  const name = profile?.full_name ?? "Your Name";
  const accent = mode === "ats" ? "#333" : template.accent;
  const headline = roleTargeted && targetRoleTitle
    ? `Targeting: ${targetRoleTitle}`
    : (targetJob ? `${targetJob}${targetCompany ? ` · ${targetCompany}` : ""}` : profile?.professional_headline);
  const sections = buildProfileSections(profile, enabledSections);

  return (
    <div style={{ fontFamily: mode === "ats" ? "Arial" : "sans-serif", fontSize: "0.72rem", background: "#fff", padding: "1.5rem", minHeight: "260mm", color: "#1a1a1a" }}>
      <div style={{ borderBottom: `3px solid ${accent}`, paddingBottom: "0.75rem", marginBottom: "1rem" }}>
        <h1 style={{ color: accent, fontSize: "1.2rem", margin: 0 }}>{name}</h1>
        {headline && <p style={{ color: "#555", marginTop: "4px", fontSize: "0.7rem" }}>{headline}</p>}
        {roleTargeted && (
          <p style={{ marginTop: "6px", fontSize: "0.65rem", color: "#888" }}>
            Role-targeted mode — enabled sections will be fully generated by AI for this role.
          </p>
        )}
      </div>
      {sections.length === 0 ? (
        <p style={{ color: "#888", fontSize: "0.75rem" }}>
          {roleTargeted ? "Toggle sections on, then generate to create AI content for this role." : "Add profile data or generate a CV to preview sections."}
        </p>
      ) : sections.map((section, i) => (
        <CVSectionBlock key={section.section_id ?? i} section={section} accent={accent} />
      ))}
    </div>
  );
}

function SectionOrderList({ sections, onChange, sectionDefs }: { sections: string[]; onChange: (s: string[]) => void; sectionDefs: { id: string; label: string }[] }) {
  const toggle = (id: string) =>
    onChange(sections.includes(id) ? sections.filter((x) => x !== id) : [...sections, id]);
  const move = (id: string, dir: -1 | 1) => {
    const idx = sections.indexOf(id);
    if (idx < 0) return;
    const next = [...sections];
    const swap = idx + dir;
    if (swap < 0 || swap >= next.length) return;
    [next[idx], next[swap]] = [next[swap], next[idx]];
    onChange(next);
  };

  const allIds = sectionDefs.map((s) => s.id);
  const ordered = [...sections, ...allIds.filter((id) => !sections.includes(id))];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
      {ordered.map((id) => {
        const sec = sectionDefs.find((s) => s.id === id);
        if (!sec) return null;
        const enabled = sections.includes(id);
        return (
          <div key={id} style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.45rem 0.5rem", borderRadius: "8px", border: "1px solid var(--border-subtle)", background: enabled ? "rgba(139,92,246,0.05)" : "transparent" }}>
            <GripVertical size={12} style={{ color: "var(--text-muted)" }} />
            <input type="checkbox" checked={enabled} onChange={() => toggle(id)} style={{ accentColor: "var(--accent-violet)" }} />
            <span style={{ flex: 1, fontSize: "0.8rem" }}>{sec.label}</span>
            {enabled && (
              <>
                <button type="button" onClick={() => move(id, -1)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)" }}><ChevronUp size={14} /></button>
                <button type="button" onClick={() => move(id, 1)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)" }}><ChevronDown size={14} /></button>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function CVBuilderPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const jobIdParam = searchParams.get("jobId");

  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get() });
  const jobsQuery = useQuery({ queryKey: ["jobs"], queryFn: () => jobApi.list() });
  const cvsQuery = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });

  const profile = profileQuery.data;
  const jobs = jobsQuery.data;
  const cvs = cvsQuery.data;

  const [selectedTemplate, setSelectedTemplate] = useState("modern");
  const [mode, setMode] = useState<PreviewMode>("visual");
  const [viewport, setViewport] = useState<ViewportMode>("desktop");
  const [enabledSections, setEnabledSections] = useState([
    "summary", "experience", "education", "skills", "certifications", "projects",
  ]);
  const [roleTargetedMode, setRoleTargetedMode] = useState(false);
  const [targetRoleTitle, setTargetRoleTitle] = useState("");
  const [targetRoleDescription, setTargetRoleDescription] = useState("");
  const [targetJobId, setTargetJobId] = useState<string>("");
  const [targetJobDescription, setTargetJobDescription] = useState("");
  const [cvName, setCvName] = useState("");
  const [tone, setTone] = useState<"concise" | "detailed" | "executive">("concise");
  const [zoom, setZoom] = useState(0.48);
  const [lastCvId, setLastCvId] = useState<string | null>(null);
  const [defaultCvId, setDefaultCvId] = useState<string | null>(localStorage.getItem(DEFAULT_CV_KEY));
  const [loadingCvId, setLoadingCvId] = useState<string | null>(null);

  const { data: generatedCv, isLoading: generatedCvLoading, isError: generatedCvError } = useQuery({
    queryKey: ["cv", lastCvId],
    queryFn: () => cvApi.get(lastCvId!),
    enabled: !!lastCvId,
  });

  const template = TEMPLATES.find((t) => t.id === selectedTemplate) ?? TEMPLATES[0];
  const selectedJob = jobs?.find((j) => j.id === targetJobId);

  const workspaceLoading = profileQuery.isLoading || jobsQuery.isLoading || cvsQuery.isLoading;
  const profileThin =
    profileQuery.isSuccess &&
    !profile?.bio_summary &&
    !profile?.professional_headline &&
    !(profile?.work_experiences?.length);

  const sectionDefs = useMemo(() => {
    const defs = [...BASE_SECTIONS];
    const customCount = profile?.custom_sections?.length ?? 0;
    if (customCount > 0) {
      const customIdx = defs.findIndex((d) => d.id === "custom");
      if (customIdx >= 0) defs[customIdx] = { ...defs[customIdx], label: `Custom sections (${customCount})` };
    }
    return defs;
  }, [profile?.custom_sections?.length]);

  useEffect(() => {
    if (jobIdParam && jobs?.length) setTargetJobId(jobIdParam);
  }, [jobIdParam, jobs]);

  useEffect(() => {
    if (selectedJob) {
      setTargetJobDescription(selectedJob.description_raw ?? "");
      if (!cvName) setCvName(`${selectedJob.title} — ${selectedJob.company_name ?? "CV"}`);
    }
  }, [selectedJob]);

  const previewContent = generatedCv?.rendered_content as Record<string, unknown> | undefined;
  const hasRendered = previewContent && Object.keys(previewContent).length > 0;

  const viewportWidth = viewport === "mobile" ? "320px" : "210mm";

  const generateMutation = useMutation({
    mutationFn: () => {
      if (roleTargetedMode && !targetRoleTitle.trim()) {
        throw new Error("role-required");
      }
      return cvApi.generate({
        name: cvName || `${profile?.full_name ?? "My"} CV`,
        target_job_id: targetJobId || undefined,
        template: template.backend,
        section_ids: enabledSections,
        tone,
        generation_mode: roleTargetedMode ? "role_targeted" : "profile",
        target_role_title: roleTargetedMode ? targetRoleTitle.trim() : undefined,
        target_role_description: roleTargetedMode
          ? (targetRoleDescription || targetJobDescription || undefined)
          : undefined,
      });
    },
    onSuccess: (cv: GeneratedCVRead) => {
      setLastCvId(cv.id);
      qc.invalidateQueries({ queryKey: ["cvs"] });
      addToast({
        type: "success",
        title: "CV generated!",
        message: roleTargetedMode
          ? `AI authored content for the ${targetRoleTitle} role.`
          : "Preview updated with AI-enhanced content from your profile.",
      });
    },
    onError: (e: any) => addToast({
      type: e?.message === "role-required" ? "info" : "error",
      message: e?.message === "role-required" ? "Enter a target role title for role-targeted generation." : "CV generation failed.",
    }),
  });

  const exportMutation = useMutation({
    mutationFn: async (format: "pdf" | "docx" | "markdown") => {
      const cvId = lastCvId ?? cvs?.[0]?.id;
      if (!cvId) throw new Error("no-cv");
      const blob = await cvApi.downloadPdf(cvId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(cvName || "cv").replace(/\s+/g, "_")}.${format === "markdown" ? "md" : format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
    onError: (e: any) =>
      addToast(e?.message === "no-cv"
        ? { type: "info", message: "Generate a CV first, then export." }
        : { type: "error", message: "Export failed." }),
  });

  const loadCV = async (cv: GeneratedCVRead) => {
    setLoadingCvId(cv.id);
    try {
      setSelectedTemplate(TEMPLATES.find((t) => t.backend === cv.template)?.id ?? cv.template);
      setEnabledSections(cv.section_config?.filter((s) => s.enabled).map((s) => s.section_id) ?? []);
      setCvName(cv.name);
      setLastCvId(cv.id);
      if (cv.target_job_id) setTargetJobId(cv.target_job_id);
      const full = await cvApi.get(cv.id);
      setLastCvId(full.id);
      addToast({ type: "info", message: `Loaded draft: ${cv.name}` });
    } catch (err) {
      addToast({ type: "error", message: queryErrorMessage(err) });
    } finally {
      setLoadingCvId(null);
    }
  };

  const setAsDefault = (id: string) => {
    localStorage.setItem(DEFAULT_CV_KEY, id);
    setDefaultCvId(id);
    addToast({ type: "success", message: "Default CV set for applications." });
  };

  const aiSuggestions = useMemo(() => {
    const suggestions: string[] = [];
    if (targetJobDescription.toLowerCase().includes("project")) suggestions.push("Enable Projects and move above Education for this role.");
    if (targetJobDescription.toLowerCase().includes("certif")) suggestions.push("Highlight Certifications — detected in the job description.");
    if (enabledSections.includes("skills") && !enabledSections.includes("projects")) suggestions.push("Consider enabling Projects to showcase applied skills.");
    if (tone === "executive") suggestions.push("Executive tone pairs well with Summary + Experience first.");
    return suggestions.length ? suggestions : ["Import a saved job or paste a JD for role-aligned section tips."];
  }, [targetJobDescription, enabledSections, tone]);

  const canGenerate = !generateMutation.isPending && !profileQuery.isLoading && !profileQuery.isError;
  const canExport = !exportMutation.isPending && Boolean(lastCvId || cvs?.[0]?.id);

  return (
    <div className="cv-studio">
      <div className="cv-studio__sidebar">
        <span className="feature-hero__eyebrow" style={{ marginBottom: "0.75rem" }}><Sparkles size={12} /> CV Builder</span>
        <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.3rem", fontWeight: 700, marginBottom: "0.25rem" }}>CV Builder</h1>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
          {roleTargetedMode
            ? "Draft mode — section toggles choose what AI writes for a target role."
            : "Profile-driven draft preview · AI can refine wording · does not invent experience."}
        </p>

        <div className="cv-studio__status" aria-live="polite">
          {workspaceLoading && (
            <div className="cv-studio__status-row cv-studio__status-row--loading">
              <Spinner size="sm" />
              <span>Loading your CV workspace…</span>
            </div>
          )}
          {profileQuery.isError && (
            <div className="cv-studio__status-row cv-studio__status-row--error" role="alert">
              <span>Profile: {queryErrorMessage(profileQuery.error)}</span>
              <Button variant="ghost" size="sm" onClick={() => profileQuery.refetch()}>Retry</Button>
            </div>
          )}
          {cvsQuery.isError && (
            <div className="cv-studio__status-row cv-studio__status-row--error" role="alert">
              <span>Saved CVs: {queryErrorMessage(cvsQuery.error)}</span>
              <Button variant="ghost" size="sm" onClick={() => cvsQuery.refetch()}>Retry</Button>
            </div>
          )}
          {jobsQuery.isError && (
            <div className="cv-studio__status-row cv-studio__status-row--error" role="alert">
              <span>Jobs: {queryErrorMessage(jobsQuery.error)}</span>
              <Button variant="ghost" size="sm" onClick={() => jobsQuery.refetch()}>Retry</Button>
            </div>
          )}
          {profileThin && (
            <div className="cv-studio__status-row cv-studio__status-row--empty">
              <span>Complete your profile first to improve CV quality.</span>
              <Link to="/profile" className="cv-studio__status-link">Open profile</Link>
            </div>
          )}
        </div>

        <Link to="/profile" style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.6rem 0.75rem", borderRadius: "10px", background: "rgba(139,92,246,0.08)", border: "1px solid var(--border-subtle)", marginBottom: "1rem", fontSize: "0.75rem", color: "var(--accent-violet-bright)", textDecoration: "none" }}>
          <User size={14} /> Edit profile data →
        </Link>

        <div style={{ display: "flex", gap: "0.5rem", padding: "0.6rem", borderRadius: "10px", background: roleTargetedMode ? "rgba(249,115,22,0.08)" : "rgba(6,182,212,0.07)", border: `1px solid ${roleTargetedMode ? "rgba(249,115,22,0.25)" : "rgba(6,182,212,0.2)"}`, marginBottom: "1.25rem", fontSize: "0.72rem", color: "var(--text-secondary)" }}>
          <Info size={13} style={{ flexShrink: 0, marginTop: "1px", color: roleTargetedMode ? "#F97316" : "var(--accent-cyan)" }} />
          {roleTargetedMode
            ? "Section toggles are on/off only. Enabled sections are drafted toward your target role."
            : "Preview uses your profile. Generate creates a saved draft; template/export polish continues in later slices."}
        </div>

        <div className="feature-glass" style={{ padding: "0.75rem", marginBottom: "1rem" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.78rem", fontWeight: 600, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={roleTargetedMode}
              onChange={(e) => setRoleTargetedMode(e.target.checked)}
              style={{ accentColor: "var(--accent-violet)" }}
            />
            Generate for a different target role
          </label>
          {roleTargetedMode && (
            <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              <Input
                label="Target role title"
                value={targetRoleTitle}
                onChange={(e) => setTargetRoleTitle(e.target.value)}
                placeholder="e.g. Senior Product Manager"
                fullWidth
              />
              <Textarea
                label="Role / JD context (optional)"
                value={targetRoleDescription}
                onChange={(e) => setTargetRoleDescription(e.target.value)}
                placeholder="Describe the role, responsibilities, or paste a job description…"
                rows={3}
                fullWidth
              />
            </div>
          )}
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <Input label="CV name" value={cvName} onChange={(e) => setCvName(e.target.value)} placeholder="e.g. Senior Engineer — Acme" fullWidth />
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <label style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "0.4rem" }}>Target job (import)</label>
          {jobsQuery.isLoading && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Loading saved jobs…</p>
          )}
          {jobsQuery.isSuccess && !jobs?.length && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
              No saved jobs found yet. You can still draft a general CV.
            </p>
          )}
          <select
            value={targetJobId}
            onChange={(e) => setTargetJobId(e.target.value)}
            disabled={jobsQuery.isLoading || jobsQuery.isError}
            style={{ width: "100%", padding: "0.55rem", borderRadius: "8px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)", color: "var(--text-primary)", fontSize: "0.8rem", marginBottom: "0.5rem" }}
          >
            <option value="">No target job</option>
            {jobs?.map((j: SavedJobRead) => <option key={j.id} value={j.id}>{j.title} — {j.company_name}</option>)}
          </select>
          <Textarea
            label="Target job description"
            value={targetJobDescription}
            onChange={(e) => setTargetJobDescription(e.target.value)}
            placeholder="Paste or import a job description to tailor keyword alignment…"
            rows={4}
            fullWidth
          />
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>SECTIONS (toggle + reorder)</p>
          <SectionOrderList sections={enabledSections} onChange={setEnabledSections} sectionDefs={sectionDefs} />
        </div>

        <div className="feature-glass" style={{ padding: "0.75rem", marginBottom: "1.25rem", fontSize: "0.72rem" }}>
          <p style={{ fontWeight: 600, marginBottom: "0.35rem", color: "var(--accent-cyan)" }}><Sparkles size={12} style={{ display: "inline", marginRight: 4 }} />Section tips (draft)</p>
          <ul style={{ margin: 0, paddingLeft: "1rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
            {aiSuggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>TEMPLATE PREVIEW ACCENTS</p>
          <p style={{ fontSize: "0.68rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
            Preview accents only — export template mapping is refined in a later slice.
          </p>
          <div className="cv-template-grid">
            {TEMPLATES.map((t) => (
              <button key={t.id} type="button" onClick={() => setSelectedTemplate(t.id)} className={`cv-template-tile${selectedTemplate === t.id ? " cv-template-tile--active" : ""}`}>
                <div className="cv-template-tile__swatch" style={{ background: t.accent }} />
                {t.label}
                <span style={{ display: "block", fontSize: "0.6rem", opacity: 0.7 }}>{t.category.toUpperCase()}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: "1.25rem" }}>
          <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>TONE</p>
          <div style={{ display: "flex", gap: "0.4rem" }}>
            {(["concise", "detailed", "executive"] as const).map((t) => (
              <button key={t} type="button" onClick={() => setTone(t)} style={{
                flex: 1, padding: "0.4rem", borderRadius: "8px", fontSize: "0.72rem", cursor: "pointer", textTransform: "capitalize",
                border: tone === t ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)",
                background: tone === t ? "rgba(139,92,246,0.08)" : "transparent",
              }}>{t}</button>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1.5rem" }}>
          <Button
            variant="primary"
            fullWidth
            onClick={() => generateMutation.mutate()}
            loading={generateMutation.isPending}
            disabled={!canGenerate}
            leftIcon={<Zap size={15} />}
          >
            {generateMutation.isPending ? "Generating draft…" : "Generate & Save draft"}
          </Button>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.4rem" }}>
            {(["pdf", "docx", "markdown"] as const).map((fmt) => (
              <Button
                key={fmt}
                variant="secondary"
                size="sm"
                onClick={() => exportMutation.mutate(fmt)}
                loading={exportMutation.isPending}
                disabled={!canExport}
                title={canExport ? `Export ${fmt}` : "Generate a draft first"}
              >
                {fmt.toUpperCase()}
              </Button>
            ))}
          </div>
          <p style={{ fontSize: "0.65rem", color: "var(--text-secondary)", margin: 0 }}>
            Export uses the last saved draft. Reliability checks continue in a later slice.
          </p>
        </div>

        <div>
          <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "0.5rem" }}>SAVED CV LIBRARY</p>
          {cvsQuery.isLoading && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 0" }}>
              <Spinner size="sm" />
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Loading saved CVs…</span>
            </div>
          )}
          {cvsQuery.isError && (
            <p role="alert" style={{ fontSize: "0.75rem", color: "var(--danger, #ef4444)", margin: 0 }}>
              We couldn&apos;t load saved CVs. Use Retry above.
            </p>
          )}
          {cvsQuery.isSuccess && !cvs?.length && (
            <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
              No saved CVs yet. Start by generating your first draft.
            </p>
          )}
          {cvsQuery.isSuccess && !!cvs?.length && (
            <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
              {cvs.map((cv) => (
                <div key={cv.id} style={{ display: "flex", alignItems: "center", gap: "0.4rem", padding: "0.5rem", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
                  <FileText size={13} style={{ color: "var(--accent-violet)" }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: "0.75rem", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{cv.name}</p>
                    <p style={{ fontSize: "0.65rem", color: "var(--text-secondary)" }}>{cv.template}</p>
                  </div>
                  {defaultCvId === cv.id && <Star size={12} style={{ color: "var(--accent-amber)" }} />}
                  <Button variant="ghost" size="sm" onClick={() => loadCV(cv)} loading={loadingCvId === cv.id} disabled={!!loadingCvId}>
                    Load
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setAsDefault(cv.id)} title="Set as default"><Star size={12} /></Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="cv-studio__viewer">
        <div className="cv-studio__toolbar">
          <span style={{ fontWeight: 700, fontSize: "0.8rem" }}>CV Preview</span>
          <Badge color="violet" size="sm">{template.label}</Badge>
          <div style={{ display: "flex", gap: "0.25rem" }}>
            {(["visual", "ats"] as const).map((m) => (
              <button key={m} type="button" onClick={() => setMode(m)} style={{ padding: "0.25rem 0.5rem", borderRadius: "6px", fontSize: "0.7rem", border: "none", cursor: "pointer", background: mode === m ? "var(--accent-violet)" : "var(--bg-overlay)", color: mode === m ? "#fff" : "var(--text-secondary)" }}>
                {m === "visual" ? "Visual" : "ATS"}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: "0.25rem", marginLeft: "0.5rem" }}>
            {([
              { id: "desktop", icon: <Monitor size={13} /> },
              { id: "mobile", icon: <Smartphone size={13} /> },
              { id: "print", icon: <Printer size={13} /> },
            ] as const).map((v) => (
              <button key={v.id} type="button" onClick={() => setViewport(v.id)} style={{ padding: "0.3rem 0.5rem", borderRadius: "6px", border: viewport === v.id ? "2px solid var(--accent-violet)" : "1px solid var(--border-subtle)", background: "transparent", cursor: "pointer", color: viewport === v.id ? "var(--accent-violet)" : "var(--text-secondary)" }}>
                {v.icon}
              </button>
            ))}
          </div>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <Button variant="ghost" size="sm" onClick={() => setZoom((z) => Math.max(0.3, z - 0.1))}><ZoomOut size={14} /></Button>
            <span style={{ fontSize: "0.7rem", minWidth: "36px", textAlign: "center" }}>{Math.round(zoom * 100)}%</span>
            <Button variant="ghost" size="sm" onClick={() => setZoom((z) => Math.min(1.2, z + 0.1))}><ZoomIn size={14} /></Button>
            <Button variant="ghost" size="sm" onClick={() => setZoom(0.48)}><RefreshCw size={14} /></Button>
          </div>
        </div>

        <div className="cv-studio__canvas">
          {generateMutation.isPending && (
            <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", background: "rgba(10,16,32,0.85)", zIndex: 10, gap: "1rem" }}>
              <div className="skeleton shimmer" style={{ width: 210, height: 297, borderRadius: 8 }} />
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Generating draft preview…</p>
            </div>
          )}
          {generatedCvLoading && !generateMutation.isPending && (
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 5 }}>
              <Spinner />
            </div>
          )}
          {generatedCvError && (
            <p role="alert" style={{ color: "var(--danger, #ef4444)", fontSize: "0.8rem", padding: "1rem" }}>
              We couldn&apos;t load this saved draft. Try Load again from the library.
            </p>
          )}
          <motion.div
            animate={{ scale: zoom }}
            style={{ transformOrigin: "top center", width: viewportWidth, minWidth: viewportWidth, boxShadow: "0 20px 60px rgba(0,0,0,0.2)", borderRadius: "4px", overflow: "hidden", position: "relative" }}
          >
            {hasRendered ? (
              <RenderedCVPreview content={previewContent!} template={template} mode={mode} />
            ) : (
              <ProfileCVPreview
                template={template}
                mode={mode}
                profile={profile}
                targetJob={selectedJob?.title ?? ""}
                targetCompany={selectedJob?.company_name ?? ""}
                enabledSections={enabledSections}
                roleTargeted={roleTargetedMode}
                targetRoleTitle={targetRoleTitle}
              />
            )}
            <div style={{ position: "absolute", bottom: "48px", left: 0, right: 0, borderTop: "2px dashed #ccc", pointerEvents: "none" }}>
              <span style={{ position: "absolute", top: "-10px", left: "50%", transform: "translateX(-50%)", background: "#fff", padding: "0 8px", fontSize: "0.6rem", color: "#999" }}>Page break</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
