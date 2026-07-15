/**
 * CVBuilderPage.tsx
 * CV Builder Studio — 15-template gallery + live preview + save/load versions (CVB-F4).
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { Eye, FileDown, Save, Sparkles, Star, FileText } from "lucide-react";
import { cvApi, jobApi, passportApi, profileApi, taxonomyApi } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useUIStore } from "@/store/ui";
import type { ApiError, CVTaxonomyMeta, GeneratedCVRead } from "@/types/api";
import {
  CVTemplateGallery,
  CV_TEMPLATE_CATALOG,
  getCVTemplate,
  type CVTemplateId,
} from "@/components/features/CVTemplateGallery";
import { CVTemplatePreview } from "@/components/features/CVTemplatePreview";
import {
  CVBuilderStudioPanel,
  type RoleIntelligencePhase,
  type RoleIntelligenceView,
} from "@/components/features/CVBuilderStudioPanel";
import {
  passportEnabledCvSectionIds,
  passportHasUsableProfile,
  passportReadinessMessage,
  passportSectionCounts,
  passportTargetsForPrefill,
} from "@/features/passport/passportIntegrationUtils";

const DEFAULT_TEMPLATE_ID: CVTemplateId = "minimal-corporate";
const STUDIO_META_SECTION = "_studio";
const TAXONOMY_META_SECTION = "_taxonomy";
const META_SECTION_IDS = new Set([STUDIO_META_SECTION, TAXONOMY_META_SECTION]);

function queryErrorMessage(err: unknown): string {
  const msg = (err as ApiError | undefined)?.message;
  return (msg && String(msg).trim()) || "We couldn't load this section. Please try again.";
}

function sanitizeFilenameToken(value: string | undefined | null, fallback: string): string {
  const cleaned = (value || "")
    .trim()
    .replace(/\s+/g, "_")
    .replace(/[^A-Za-z0-9_-]/g, "")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return cleaned || fallback;
}

/** CareerKundi_<CandidateName>_<TemplateName>_CV.pdf */
function buildSafeCvPdfFilename(candidateName: string | undefined | null, templateName: string): string {
  const name = sanitizeFilenameToken(candidateName, "Candidate");
  const template = sanitizeFilenameToken(templateName, "Template");
  return `CareerKundi_${name}_${template}_CV.pdf`;
}

function isCVTemplateId(value: string | null | undefined): value is CVTemplateId {
  return Boolean(value && CV_TEMPLATE_CATALOG.some((t) => t.id === value));
}

/** Restore gallery id from saved CV; older rows without studio id use default. */
function resolveLoadedTemplateId(cv: GeneratedCVRead): {
  templateId: CVTemplateId;
  usedDefault: boolean;
} {
  if (isCVTemplateId(cv.studio_template_id)) {
    return { templateId: cv.studio_template_id, usedDefault: false };
  }
  const fromMeta = cv.section_config?.find((s) => s.section_id === STUDIO_META_SECTION)?.studio_template_id;
  if (isCVTemplateId(fromMeta)) {
    return { templateId: fromMeta, usedDefault: false };
  }
  const byBackend = CV_TEMPLATE_CATALOG.find((t) => t.backendTemplate === cv.template);
  if (byBackend) {
    return { templateId: byBackend.id, usedDefault: true };
  }
  return { templateId: DEFAULT_TEMPLATE_ID, usedDefault: true };
}

function enabledSectionIdsFromCv(cv: GeneratedCVRead): string[] {
  return (cv.section_config ?? [])
    .filter((s) => s.enabled && !META_SECTION_IDS.has(s.section_id))
    .map((s) => s.section_id);
}

function extractTaxonomyMetaFromCv(cv: GeneratedCVRead): CVTaxonomyMeta | null {
  const row = cv.section_config?.find((s) => s.section_id === TAXONOMY_META_SECTION);
  if (!row) return null;
  return {
    target_role_text: row.target_role_text ?? null,
    matched_role_id: row.matched_role_id ?? null,
    matched_skill_id: row.matched_skill_id ?? null,
    normalized_text: row.normalized_text ?? null,
    source: row.source ?? null,
    confidence: row.confidence ?? null,
    explanation: row.explanation ?? null,
    accepted_by_user: Boolean(row.accepted_by_user),
    kept_freeform: Boolean(row.kept_freeform),
    matched_role_title: row.matched_role_title ?? null,
  };
}

function phaseFromTaxonomyMeta(meta: CVTaxonomyMeta | null, roleText: string): RoleIntelligencePhase {
  if (!roleText.trim()) return "empty";
  if (!meta) return "ready";
  if (meta.accepted_by_user) return "accepted";
  if (meta.kept_freeform) return "kept_freeform";
  if (meta.matched_role_id) return "suggested";
  if ((meta.confidence || "").toLowerCase() === "unknown" || !meta.matched_role_id) {
    return "unknown";
  }
  return "ready";
}

const DEFAULT_CV_KEY = "ck_default_cv_id";

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

export default function CVBuilderPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const jobIdParam = searchParams.get("jobId");
  const previewRef = useRef<HTMLDivElement>(null);

  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get() });
  const jobsQuery = useQuery({ queryKey: ["jobs"], queryFn: () => jobApi.list() });
  const cvsQuery = useQuery({ queryKey: ["cvs"], queryFn: () => cvApi.list() });
  const passportQuery = useQuery({
    queryKey: ["passport", "aggregate"],
    queryFn: () => passportApi.get(),
    retry: false,
  });

  const profile = profileQuery.data;
  const jobs = jobsQuery.data;
  const cvs = cvsQuery.data;
  const [passportRoleNote, setPassportRoleNote] = useState<string | null>(null);

  const [selectedTemplateId, setSelectedTemplateId] = useState<CVTemplateId>(DEFAULT_TEMPLATE_ID);
  const [selectedCvId, setSelectedCvId] = useState<string | null>(null);
  const [enabledSections, setEnabledSections] = useState([
    "summary", "experience", "education", "skills", "certifications", "projects",
  ]);
  const [targetJobId, setTargetJobId] = useState("");
  const [targetJobDescription, setTargetJobDescription] = useState("");
  const [cvName, setCvName] = useState("");
  const [tone, setTone] = useState<"concise" | "detailed" | "executive">("concise");
  const [defaultCvId, setDefaultCvId] = useState<string | null>(localStorage.getItem(DEFAULT_CV_KEY));
  const [loadingCvId, setLoadingCvId] = useState<string | null>(null);
  const [isSavingDraft, setIsSavingDraft] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadSuccess, setLoadSuccess] = useState<string | null>(null);
  const [templateRestoredNote, setTemplateRestoredNote] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [roleText, setRoleText] = useState("");
  const [roleIntelPhase, setRoleIntelPhase] = useState<RoleIntelligencePhase>("empty");
  const [taxonomyMeta, setTaxonomyMeta] = useState<CVTaxonomyMeta | null>(null);
  const [matchedRoleTitle, setMatchedRoleTitle] = useState<string | null>(null);
  const roleTextAutoFromJobRef = useRef(true);

  const template = getCVTemplate(selectedTemplateId);
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

  const roleIntelligence: RoleIntelligenceView = useMemo(
    () => ({
      phase: roleIntelPhase,
      targetRoleText: roleText,
      matchedRoleId: taxonomyMeta?.matched_role_id ?? null,
      matchedRoleTitle: matchedRoleTitle || taxonomyMeta?.matched_role_title || null,
      source: (taxonomyMeta?.source as string | null) ?? null,
      confidence: (taxonomyMeta?.confidence as string | null) ?? null,
      explanation: taxonomyMeta?.explanation ?? null,
    }),
    [roleIntelPhase, roleText, taxonomyMeta, matchedRoleTitle],
  );

  useEffect(() => {
    if (jobIdParam && jobs?.length) setTargetJobId(jobIdParam);
  }, [jobIdParam, jobs]);

  useEffect(() => {
    if (selectedJob) {
      setTargetJobDescription(selectedJob.description_raw ?? "");
      if (!cvName) setCvName(`${selectedJob.title} — ${selectedJob.company_name ?? "CV"}`);
      if (roleTextAutoFromJobRef.current) {
        const title = (selectedJob.title || "").trim();
        if (title) {
          setRoleText(title);
          setRoleIntelPhase("ready");
          setTaxonomyMeta(null);
          setMatchedRoleTitle(null);
        }
      }
    }
  }, [selectedJob]);

  const handleRoleTextChange = (value: string) => {
    roleTextAutoFromJobRef.current = false;
    setRoleText(value);
    setTaxonomyMeta(null);
    setMatchedRoleTitle(null);
    setRoleIntelPhase(value.trim() ? "ready" : "empty");
  };

  const buildTaxonomyPayload = (): CVTaxonomyMeta | undefined => {
    if (!taxonomyMeta) return undefined;
    return {
      ...taxonomyMeta,
      target_role_text: roleText.trim() || taxonomyMeta.target_role_text || null,
      matched_role_title: matchedRoleTitle || taxonomyMeta.matched_role_title || null,
    };
  };

  const checkRoleMatch = async () => {
    const text = roleText.trim();
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
      if (match.matched_role_id) {
        try {
          const role = await taxonomyApi.getRole(match.matched_role_id);
          title = role.title;
        } catch {
          title = match.matched_role_id;
        }
      }
      const meta: CVTaxonomyMeta = {
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
      };
      setTaxonomyMeta(meta);
      setMatchedRoleTitle(title);
      setRoleIntelPhase(match.matched_role_id ? "suggested" : "unknown");
    } catch {
      setRoleIntelPhase("unavailable");
      setTaxonomyMeta(null);
      setMatchedRoleTitle(null);
    }
  };

  const acceptSuggestedRole = () => {
    if (!taxonomyMeta?.matched_role_id) return;
    const canonical =
      matchedRoleTitle || taxonomyMeta.matched_role_title || taxonomyMeta.matched_role_id;
    roleTextAutoFromJobRef.current = false;
    setRoleText(canonical);
    const next: CVTaxonomyMeta = {
      ...taxonomyMeta,
      target_role_text: canonical,
      accepted_by_user: true,
      kept_freeform: false,
      matched_role_title: canonical,
    };
    setTaxonomyMeta(next);
    setMatchedRoleTitle(canonical);
    setRoleIntelPhase("accepted");
  };

  const keepFreeform = () => {
    const text = roleText.trim();
    const next: CVTaxonomyMeta = {
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
      matched_role_title: matchedRoleTitle || taxonomyMeta?.matched_role_title || null,
    };
    setTaxonomyMeta(next);
    setRoleIntelPhase("kept_freeform");
  };

  const recheckRole = () => {
    setTaxonomyMeta(null);
    setMatchedRoleTitle(null);
    setRoleIntelPhase(roleText.trim() ? "ready" : "empty");
  };

  const saveDraft = async () => {
    if (!profile && profileQuery.isError) {
      setSaveError("Could not save this CV. Please try again.");
      return;
    }
    setSaveError(null);
    setSaveSuccess(null);
    setIsSavingDraft(true);
    try {
      const name = cvName || `${profile?.full_name ?? "My"} CV`;
      const taxonomy = buildTaxonomyPayload();
      const payload = {
        name,
        target_job_id: targetJobId || undefined,
        template: template.backendTemplate,
        studio_template_id: selectedTemplateId,
        section_ids: enabledSections.filter((id) => !META_SECTION_IDS.has(id)),
        tone,
        generation_mode: "profile" as const,
        ...(taxonomy ? { taxonomy } : {}),
      };

      let cv: GeneratedCVRead;
      if (selectedCvId) {
        cv = await cvApi.update(selectedCvId, {
          name: payload.name,
          template: payload.template,
          studio_template_id: payload.studio_template_id,
          section_ids: payload.section_ids,
          ...(taxonomy ? { taxonomy } : {}),
        });
        setSaveSuccess("Draft saved");
        addToast({
          type: "success",
          title: "Draft saved",
          message: "Updated this CV version (name, sections, and selected template).",
        });
      } else {
        cv = await cvApi.generate(payload);
        setSaveSuccess("Draft saved");
        addToast({
          type: "success",
          title: "Draft saved",
          message: "Created a new saved CV version with the selected template.",
        });
      }
      setSelectedCvId(cv.id);
      const restored = extractTaxonomyMetaFromCv(cv);
      if (restored) {
        setTaxonomyMeta(restored);
        setMatchedRoleTitle(restored.matched_role_title ?? null);
        setRoleText((restored.target_role_text || roleText).trim());
        setRoleIntelPhase(phaseFromTaxonomyMeta(restored, restored.target_role_text || roleText));
      }
      await qc.invalidateQueries({ queryKey: ["cvs"] });
    } catch (err) {
      const message = "Could not save this CV. Please try again.";
      setSaveError(message);
      setSaveSuccess(null);
      addToast({ type: "error", message: queryErrorMessage(err) || message });
    } finally {
      setIsSavingDraft(false);
    }
  };

  const exportMutation = useMutation({
    mutationFn: async () => {
      const cvId = selectedCvId ?? cvs?.[0]?.id;
      if (!cvId) throw new Error("no-cv");
      setExportError(null);
      setExportSuccess(null);
      const blob = await cvApi.downloadPdf(cvId, "pdf", { templateId: selectedTemplateId });
      if (!(blob instanceof Blob) || blob.size === 0) {
        throw new Error("empty-pdf");
      }
      if (blob.type && blob.type.includes("application/json")) {
        throw new Error("export-rejected");
      }
      const filename = buildSafeCvPdfFilename(
        profile?.full_name || cvName || "Candidate",
        template.name,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      return filename;
    },
    onSuccess: (filename) => {
      setExportSuccess(`Downloaded ${filename}`);
      addToast({
        type: "success",
        title: "PDF exported",
        message: "Download started. PDF uses a mapped style family for the selected studio template.",
      });
    },
    onError: (e: unknown) => {
      const code = (e as Error)?.message;
      const message =
        code === "no-cv"
          ? "Generate or select a CV draft before exporting."
          : code === "empty-pdf"
            ? "Export returned an empty file. Please try again."
            : "We couldn't export this PDF. Please try again.";
      setExportError(message);
      setExportSuccess(null);
      addToast({ type: code === "no-cv" ? "info" : "error", message });
    },
  });

  const loadCV = async (cv: GeneratedCVRead) => {
    setLoadingCvId(cv.id);
    setLoadError(null);
    setLoadSuccess(null);
    setTemplateRestoredNote(null);
    try {
      const full = await cvApi.get(cv.id);
      const { templateId, usedDefault } = resolveLoadedTemplateId(full);
      setSelectedTemplateId(templateId);
      setEnabledSections(enabledSectionIdsFromCv(full));
      setCvName(full.name);
      setSelectedCvId(full.id);
      if (full.target_job_id) setTargetJobId(full.target_job_id);
      const tax = extractTaxonomyMetaFromCv(full);
      if (tax) {
        roleTextAutoFromJobRef.current = false;
        const text = (tax.target_role_text || "").trim();
        setRoleText(text);
        setTaxonomyMeta(tax);
        setMatchedRoleTitle(tax.matched_role_title ?? null);
        setRoleIntelPhase(phaseFromTaxonomyMeta(tax, text));
      } else {
        roleTextAutoFromJobRef.current = true;
        setRoleText("");
        setTaxonomyMeta(null);
        setMatchedRoleTitle(null);
        setRoleIntelPhase("empty");
      }
      setLoadSuccess("Loaded saved CV");
      if (usedDefault) {
        setTemplateRestoredNote("Older CV version uses default template.");
      } else {
        setTemplateRestoredNote("Template restored from saved version.");
      }
      addToast({ type: "info", message: `Loaded draft: ${full.name}` });
    } catch (err) {
      setLoadError("Could not load this CV.");
      setLoadSuccess(null);
      addToast({ type: "error", message: queryErrorMessage(err) });
    } finally {
      setLoadingCvId(null);
    }
  };

  const scrollToPreview = () => {
    previewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const canSave = !isSavingDraft && !profileQuery.isLoading && !profileQuery.isError;
  const canExport = !exportMutation.isPending && Boolean(selectedCvId || cvs?.[0]?.id);

  return (
    <div className="cv-builder-studio">
      <header className="cv-builder-studio__header">
        <div>
          <p className="cv-builder-studio__eyebrow">
            <Sparkles size={12} /> CV Builder Studio
          </p>
          <h1>Design a distinctive CV</h1>
          <p>
            Modern layered studio with {CV_TEMPLATE_CATALOG.length} structurally different templates
            and a live preview engine. Save Draft stores the selected gallery template with the CV
            version. PDF export maps to a supported style family (modern / classic / compact / creative).
          </p>
        </div>
        <div className="cv-builder-studio__actions">
          <Button variant="secondary" leftIcon={<Eye size={15} />} onClick={scrollToPreview}>
            Preview
          </Button>
          <Button
            variant="primary"
            leftIcon={<Save size={15} />}
            loading={isSavingDraft}
            disabled={!canSave}
            onClick={() => void saveDraft()}
          >
            {isSavingDraft ? "Saving..." : "Save Draft"}
          </Button>
          <Button
            variant="secondary"
            leftIcon={<FileDown size={15} />}
            loading={exportMutation.isPending}
            disabled={!canExport}
            onClick={() => exportMutation.mutate()}
            title={
              canExport
                ? `Export PDF (${template.name} → ${template.backendTemplate} style)`
                : "Generate or select a CV before exporting"
            }
          >
            {exportMutation.isPending ? "Exporting..." : "Export PDF"}
          </Button>
        </div>
      </header>

      <div className="cv-builder-save-load" aria-live="polite">
        {isSavingDraft && (
          <div className="cv-builder-save-status">Saving…</div>
        )}
        {saveError && (
          <div className="cv-builder-save-error" role="alert">{saveError}</div>
        )}
        {saveSuccess && !saveError && (
          <div className="cv-builder-save-success">{saveSuccess}</div>
        )}
        {loadError && (
          <div className="cv-builder-save-error" role="alert">{loadError}</div>
        )}
        {loadSuccess && !loadError && (
          <div className="cv-builder-save-success">{loadSuccess}</div>
        )}
        {templateRestoredNote && !loadError && (
          <div className="cv-builder-save-status">{templateRestoredNote}</div>
        )}
        {selectedCvId && (
          <p className="cv-builder-save-load__selected">
            Selected version: <strong>{selectedCvId.slice(0, 8)}…</strong>
            {" · "}
            Template: <strong>{template.name}</strong>
          </p>
        )}
      </div>

      <div className="cv-builder-export" aria-live="polite">
        {exportMutation.isPending && (
          <div className="cv-builder-export-status">Exporting PDF…</div>
        )}
        {exportError && (
          <div className="cv-builder-export-error" role="alert">{exportError}</div>
        )}
        {exportSuccess && !exportError && (
          <div className="cv-builder-export-success">{exportSuccess}</div>
        )}
        <p className="cv-builder-export-note">
          PDF uses mapped backend style <strong>{template.backendTemplate}</strong> for selected
          template <strong>{template.name}</strong>. Studio preview layouts are richer than PDF CSS families.
        </p>
      </div>

      <div className="cv-builder-studio__status" aria-live="polite">
        {workspaceLoading && (
          <div className="cv-builder-studio__status-row cv-builder-studio__status-row--loading">
            <Spinner size="sm" />
            <span>Loading your CV workspace…</span>
          </div>
        )}
        {profileQuery.isError && (
          <div className="cv-builder-studio__status-row cv-builder-studio__status-row--error" role="alert">
            <span>Profile: {queryErrorMessage(profileQuery.error)}</span>
            <Button variant="ghost" size="sm" onClick={() => profileQuery.refetch()}>Retry</Button>
          </div>
        )}
        {cvsQuery.isError && (
          <div className="cv-builder-studio__status-row cv-builder-studio__status-row--error" role="alert">
            <span>Saved CVs: {queryErrorMessage(cvsQuery.error)}</span>
            <Button variant="ghost" size="sm" onClick={() => cvsQuery.refetch()}>Retry</Button>
          </div>
        )}
        {jobsQuery.isError && (
          <div className="cv-builder-studio__status-row cv-builder-studio__status-row--error" role="alert">
            <span>Jobs: {queryErrorMessage(jobsQuery.error)}</span>
            <Button variant="ghost" size="sm" onClick={() => jobsQuery.refetch()}>Retry</Button>
          </div>
        )}
        {profileThin && (
          <div className="cv-builder-studio__status-row cv-builder-studio__status-row--empty">
            <span>Complete your profile first to improve CV quality.</span>
            <Link to="/profile">Open profile</Link>
          </div>
        )}
      </div>

      <section
        className="cv-builder-studio__status"
        aria-label="Career Passport for CV"
        data-testid="cv-passport-card"
        style={{
          marginBottom: "1rem",
          padding: "0.9rem 1rem",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          background: "var(--bg-elevated)",
        }}
      >
        <strong style={{ display: "block", marginBottom: "0.35rem" }}>
          Career Passport available
        </strong>
        <p style={{ margin: "0 0 0.5rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          Private and unverified. CV drafts use your private Passport/profile data.
        </p>
        {passportQuery.isLoading && (
          <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Loading Passport…
          </p>
        )}
        {passportQuery.isError && (
          <p role="status" style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            Career Passport could not be loaded. You can still build a CV from your profile.
          </p>
        )}
        {passportQuery.isSuccess && (
          <>
            <p style={{ margin: "0 0 0.5rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              {passportReadinessMessage(passportQuery.data)}
            </p>
            {passportHasUsableProfile(passportQuery.data) ? (
              <>
                <p style={{ margin: "0 0 0.5rem", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                  {(() => {
                    const c = passportSectionCounts(passportQuery.data);
                    return `Usable sections — summary ${c.profile}, experience ${c.experience}, education ${c.education}, skills ${c.skills}, projects ${c.projects}, certifications ${c.credentials}.`;
                  })()}
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    onClick={() => {
                      const ids = passportEnabledCvSectionIds(passportQuery.data);
                      if (ids.length) setEnabledSections(ids);
                    }}
                  >
                    Use Passport sections for this CV
                  </Button>
                  <Link to="/passport">
                    <Button type="button" size="sm" variant="ghost">
                      Edit in Career Passport
                    </Button>
                  </Link>
                </div>
                {passportTargetsForPrefill(passportQuery.data).length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      Prefill role from Passport target:
                    </span>
                    {passportTargetsForPrefill(passportQuery.data).slice(0, 4).map((t) => (
                      <Button
                        key={t.id}
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setRoleText(t.target_role_text);
                          roleTextAutoFromJobRef.current = false;
                          setRoleIntelPhase(t.target_role_text.trim() ? "ready" : "empty");
                          setTaxonomyMeta(null);
                          setPassportRoleNote(
                            `Role text prefilled from Passport target “${t.target_role_text}”. Private and unverified.`,
                          );
                        }}
                      >
                        {t.target_role_text}
                      </Button>
                    ))}
                  </div>
                )}
                {passportRoleNote && (
                  <p style={{ margin: "0.5rem 0 0", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {passportRoleNote}
                  </p>
                )}
              </>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                <Link to="/passport">
                  <Button type="button" size="sm" variant="secondary">
                    Edit in Career Passport
                  </Button>
                </Link>
              </div>
            )}
          </>
        )}
      </section>

      <div className="cv-builder-studio__body">
        <CVTemplateGallery selectedId={selectedTemplateId} onSelect={setSelectedTemplateId} />

        <section className="cv-builder-studio__preview-pane" ref={previewRef} aria-label="Live CV preview">
          <div className="cv-builder-studio__preview-toolbar">
            <strong>Live preview</strong>
            <span>{template.name}</span>
            <span className="cv-builder-studio__preview-ats">{template.atsLevel} ATS</span>
          </div>
          <div className="cv-builder-studio__preview-stage">
            <CVTemplatePreview template={template} profile={profile} />
          </div>
        </section>

        <CVBuilderStudioPanel
          template={template}
          cvName={cvName}
          onCvNameChange={setCvName}
          tone={tone}
          onToneChange={setTone}
          enabledSections={enabledSections}
          onSectionsChange={setEnabledSections}
          sectionDefs={sectionDefs}
          targetJobId={targetJobId}
          onTargetJobIdChange={setTargetJobId}
          targetJobDescription={targetJobDescription}
          onTargetJobDescriptionChange={setTargetJobDescription}
          jobs={jobs}
          jobsLoading={jobsQuery.isLoading}
          jobsError={jobsQuery.isError}
          jobsEmpty={jobsQuery.isSuccess && !jobs?.length}
          roleIntelligence={roleIntelligence}
          onRoleTextChange={handleRoleTextChange}
          onCheckRoleMatch={() => void checkRoleMatch()}
          onAcceptSuggestedRole={acceptSuggestedRole}
          onKeepFreeform={keepFreeform}
          onRecheckRole={recheckRole}
        />
      </div>

      <section className="cv-builder-studio__library cv-builder-version-list" aria-label="Saved CV library">
        <h2>Saved drafts</h2>
        {cvsQuery.isLoading && (
          <div className="cv-builder-studio__library-loading">
            <Spinner size="sm" /> Loading saved CVs…
          </div>
        )}
        {cvsQuery.isSuccess && !cvs?.length && (
          <p>No saved CVs yet. Start by saving your first draft.</p>
        )}
        {cvsQuery.isSuccess && !!cvs?.length && (
          <ul>
            {cvs.map((cv) => {
              const loaded = resolveLoadedTemplateId(cv);
              const isSelected = selectedCvId === cv.id;
              return (
                <li
                  key={cv.id}
                  className={`cv-builder-version-card${isSelected ? " is-selected" : ""}`}
                >
                  <FileText size={14} />
                  <div>
                    <strong>{cv.name}</strong>
                    <span>
                      {getCVTemplate(loaded.templateId).name}
                      {loaded.usedDefault && !cv.studio_template_id ? " · default template" : ""}
                    </span>
                  </div>
                  {defaultCvId === cv.id && <Star size={12} className="is-default" />}
                  <Button
                    variant={isSelected ? "secondary" : "ghost"}
                    size="sm"
                    loading={loadingCvId === cv.id}
                    disabled={!!loadingCvId}
                    onClick={() => void loadCV(cv)}
                  >
                    {isSelected ? "Selected" : "Load"}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      localStorage.setItem(DEFAULT_CV_KEY, cv.id);
                      setDefaultCvId(cv.id);
                      addToast({ type: "success", message: "Default CV set for applications." });
                    }}
                  >
                    Default
                  </Button>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
