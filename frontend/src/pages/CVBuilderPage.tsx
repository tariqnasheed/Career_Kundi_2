/**
 * CVBuilderPage.tsx
 * CV Builder Studio — 15-template gallery + live preview engine (CVB-F2).
 * PDF export hardening and version persistence continue in later slices.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { Eye, FileDown, Save, Sparkles, Star, FileText } from "lucide-react";
import { cvApi, jobApi, profileApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";
import type { ApiError, GeneratedCVRead } from "../types/api";
import {
  CVTemplateGallery,
  CV_TEMPLATE_CATALOG,
  getCVTemplate,
  type CVTemplateId,
} from "../components/features/CVTemplateGallery";
import { CVTemplatePreview } from "../components/features/CVTemplatePreview";
import { CVBuilderStudioPanel } from "../components/features/CVBuilderStudioPanel";

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

  const profile = profileQuery.data;
  const jobs = jobsQuery.data;
  const cvs = cvsQuery.data;

  const [selectedTemplateId, setSelectedTemplateId] = useState<CVTemplateId>("minimal-corporate");
  const [enabledSections, setEnabledSections] = useState([
    "summary", "experience", "education", "skills", "certifications", "projects",
  ]);
  const [targetJobId, setTargetJobId] = useState("");
  const [targetJobDescription, setTargetJobDescription] = useState("");
  const [cvName, setCvName] = useState("");
  const [tone, setTone] = useState<"concise" | "detailed" | "executive">("concise");
  const [lastCvId, setLastCvId] = useState<string | null>(null);
  const [defaultCvId, setDefaultCvId] = useState<string | null>(localStorage.getItem(DEFAULT_CV_KEY));
  const [loadingCvId, setLoadingCvId] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

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

  useEffect(() => {
    if (jobIdParam && jobs?.length) setTargetJobId(jobIdParam);
  }, [jobIdParam, jobs]);

  useEffect(() => {
    if (selectedJob) {
      setTargetJobDescription(selectedJob.description_raw ?? "");
      if (!cvName) setCvName(`${selectedJob.title} — ${selectedJob.company_name ?? "CV"}`);
    }
  }, [selectedJob]);

  const generateMutation = useMutation({
    mutationFn: () =>
      cvApi.generate({
        name: cvName || `${profile?.full_name ?? "My"} CV`,
        target_job_id: targetJobId || undefined,
        template: template.backendTemplate,
        section_ids: enabledSections,
        tone,
        generation_mode: "profile",
      }),
    onSuccess: (cv: GeneratedCVRead) => {
      setLastCvId(cv.id);
      qc.invalidateQueries({ queryKey: ["cvs"] });
      addToast({
        type: "success",
        title: "Draft saved",
        message: "Saved via existing generate API. Version UX continues in a later slice.",
      });
    },
    onError: () => addToast({ type: "error", message: "Could not save draft." }),
  });

  const exportMutation = useMutation({
    mutationFn: async () => {
      const cvId = lastCvId ?? cvs?.[0]?.id;
      if (!cvId) throw new Error("no-cv");
      setExportError(null);
      setExportSuccess(null);
      const blob = await cvApi.downloadPdf(cvId, "pdf", { templateId: selectedTemplateId });
      if (!(blob instanceof Blob) || blob.size === 0) {
        throw new Error("empty-pdf");
      }
      // Guard against API error JSON returned as blob
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
    try {
      const match = CV_TEMPLATE_CATALOG.find((t) => t.backendTemplate === cv.template);
      if (match) setSelectedTemplateId(match.id);
      setEnabledSections(cv.section_config?.filter((s) => s.enabled).map((s) => s.section_id) ?? []);
      setCvName(cv.name);
      setLastCvId(cv.id);
      if (cv.target_job_id) setTargetJobId(cv.target_job_id);
      await cvApi.get(cv.id);
      addToast({ type: "info", message: `Loaded draft: ${cv.name}` });
    } catch (err) {
      addToast({ type: "error", message: queryErrorMessage(err) });
    } finally {
      setLoadingCvId(null);
    }
  };

  const scrollToPreview = () => {
    previewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const canSave = !generateMutation.isPending && !profileQuery.isLoading && !profileQuery.isError;
  const canExport = !exportMutation.isPending && Boolean(lastCvId || cvs?.[0]?.id);

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
            and a live preview engine. PDF export maps the selected template to a supported style
            family (modern / classic / compact / creative). Full layout-parity PDF rendering is deferred.
          </p>
        </div>
        <div className="cv-builder-studio__actions">
          <Button variant="secondary" leftIcon={<Eye size={15} />} onClick={scrollToPreview}>
            Preview
          </Button>
          <Button
            variant="primary"
            leftIcon={<Save size={15} />}
            loading={generateMutation.isPending}
            disabled={!canSave}
            onClick={() => generateMutation.mutate()}
          >
            Save Draft
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
        />
      </div>

      <section className="cv-builder-studio__library" aria-label="Saved CV library">
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
            {cvs.map((cv) => (
              <li key={cv.id}>
                <FileText size={14} />
                <div>
                  <strong>{cv.name}</strong>
                  <span>{cv.template}</span>
                </div>
                {defaultCvId === cv.id && <Star size={12} className="is-default" />}
                <Button
                  variant="ghost"
                  size="sm"
                  loading={loadingCvId === cv.id}
                  disabled={!!loadingCvId}
                  onClick={() => loadCV(cv)}
                >
                  Load
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
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
