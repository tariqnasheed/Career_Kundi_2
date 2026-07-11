/**
 * CVBuilderStudioPanel.tsx — right-side content/style controls (CVB-F2).
 */

import { Link } from "react-router-dom";
import { User } from "lucide-react";
import { Input, Textarea } from "../ui/Input";
import type { CVTemplateMeta } from "./CVTemplateGallery";
import type { SavedJobRead } from "../../types/api";

interface SectionDef {
  id: string;
  label: string;
}

interface CVBuilderStudioPanelProps {
  template: CVTemplateMeta;
  cvName: string;
  onCvNameChange: (v: string) => void;
  tone: "concise" | "detailed" | "executive";
  onToneChange: (v: "concise" | "detailed" | "executive") => void;
  enabledSections: string[];
  onSectionsChange: (ids: string[]) => void;
  sectionDefs: SectionDef[];
  targetJobId: string;
  onTargetJobIdChange: (id: string) => void;
  targetJobDescription: string;
  onTargetJobDescriptionChange: (v: string) => void;
  jobs: SavedJobRead[] | undefined;
  jobsLoading: boolean;
  jobsError: boolean;
  jobsEmpty: boolean;
}

export function CVBuilderStudioPanel({
  template,
  cvName,
  onCvNameChange,
  tone,
  onToneChange,
  enabledSections,
  onSectionsChange,
  sectionDefs,
  targetJobId,
  onTargetJobIdChange,
  targetJobDescription,
  onTargetJobDescriptionChange,
  jobs,
  jobsLoading,
  jobsError,
  jobsEmpty,
}: CVBuilderStudioPanelProps) {
  const toggle = (id: string) => {
    onSectionsChange(
      enabledSections.includes(id)
        ? enabledSections.filter((x) => x !== id)
        : [...enabledSections, id],
    );
  };

  return (
    <aside className="cv-builder-studio-panel" aria-label="CV content and style controls">
      <div className="cv-builder-studio-panel__meta">
        <p className="cv-builder-studio-panel__eyebrow">Selected template</p>
        <h2>{template.name}</h2>
        <p className="cv-builder-studio-panel__desc">{template.description}</p>
        <dl className="cv-builder-studio-panel__facts">
          <div><dt>Category</dt><dd>{template.category}</dd></div>
          <div><dt>Best for</dt><dd>{template.bestFor}</dd></div>
          <div><dt>Layout</dt><dd>{template.layoutStyle}</dd></div>
          <div><dt>ATS / readability</dt><dd>{template.atsLevel}</dd></div>
          <div><dt>Accent</dt><dd>{template.accent}</dd></div>
        </dl>
        <div className="cv-builder-studio-panel__strengths">
          {template.strengths.map((s) => (
            <span key={s}>{s}</span>
          ))}
        </div>
      </div>

      <Link to="/profile" className="cv-builder-studio-panel__profile-link">
        <User size={14} /> Edit profile data →
      </Link>

      <div className="cv-builder-studio-panel__field">
        <Input
          label="Draft name"
          value={cvName}
          onChange={(e) => onCvNameChange(e.target.value)}
          placeholder="e.g. Backend Engineer — Acme"
          fullWidth
        />
      </div>

      <div className="cv-builder-studio-panel__field">
        <p className="cv-builder-studio-panel__label">Tone</p>
        <div className="cv-builder-studio-panel__tone">
          {(["concise", "detailed", "executive"] as const).map((t) => (
            <button
              key={t}
              type="button"
              className={tone === t ? "is-active" : undefined}
              onClick={() => onToneChange(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="cv-builder-studio-panel__field">
        <p className="cv-builder-studio-panel__label">Sections</p>
        <div className="cv-builder-studio-panel__sections">
          {sectionDefs.map((sec) => (
            <label key={sec.id}>
              <input
                type="checkbox"
                checked={enabledSections.includes(sec.id)}
                onChange={() => toggle(sec.id)}
              />
              {sec.label}
            </label>
          ))}
        </div>
      </div>

      <div className="cv-builder-studio-panel__field">
        <p className="cv-builder-studio-panel__label">Target job (optional)</p>
        {jobsLoading && <p className="cv-builder-studio-panel__hint">Loading saved jobs…</p>}
        {jobsEmpty && (
          <p className="cv-builder-studio-panel__hint">No saved jobs yet. You can still draft a general CV.</p>
        )}
        {jobsError && (
          <p className="cv-builder-studio-panel__hint cv-builder-studio-panel__hint--error">
            We couldn&apos;t load saved jobs.
          </p>
        )}
        <select
          value={targetJobId}
          onChange={(e) => onTargetJobIdChange(e.target.value)}
          disabled={jobsLoading || jobsError}
        >
          <option value="">No target job</option>
          {jobs?.map((j) => (
            <option key={j.id} value={j.id}>
              {j.title} — {j.company_name}
            </option>
          ))}
        </select>
        <Textarea
          label="Job description context"
          value={targetJobDescription}
          onChange={(e) => onTargetJobDescriptionChange(e.target.value)}
          placeholder="Paste a JD for keyword alignment (optional)"
          rows={3}
          fullWidth
        />
      </div>

      <p className="cv-builder-studio-panel__footnote">
        Preview accents are frontend layouts. PDF export fidelity is verified in a later slice.
      </p>
    </aside>
  );
}
