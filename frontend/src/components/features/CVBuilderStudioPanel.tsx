/**
 * CVBuilderStudioPanel.tsx — right-side content/style controls (CVB-F2)
 * + advisory Role Intelligence card (0051-F8).
 */

import { Link } from "react-router-dom";
import { User } from "lucide-react";
import { Input, Textarea } from "../ui/Input";
import { Button } from "../ui/Button";
import type { CVTemplateMeta } from "./CVTemplateGallery";
import type { SavedJobRead } from "../../types/api";

interface SectionDef {
  id: string;
  label: string;
}

export type RoleIntelligencePhase =
  | "empty"
  | "ready"
  | "loading"
  | "suggested"
  | "unknown"
  | "accepted"
  | "kept_freeform"
  | "unavailable";

export interface RoleIntelligenceView {
  phase: RoleIntelligencePhase;
  targetRoleText: string;
  matchedRoleId: string | null;
  matchedRoleTitle: string | null;
  source: string | null;
  confidence: string | null;
  explanation: string | null;
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
  roleIntelligence: RoleIntelligenceView;
  onRoleTextChange: (v: string) => void;
  onCheckRoleMatch: () => void;
  onAcceptSuggestedRole: () => void;
  onKeepFreeform: () => void;
  onRecheckRole: () => void;
}

function formatLabel(value: string | null): string {
  if (!value) return "—";
  return value.replace(/_/g, " ");
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
  roleIntelligence,
  onRoleTextChange,
  onCheckRoleMatch,
  onAcceptSuggestedRole,
  onKeepFreeform,
  onRecheckRole,
}: CVBuilderStudioPanelProps) {
  const toggle = (id: string) => {
    onSectionsChange(
      enabledSections.includes(id)
        ? enabledSections.filter((x) => x !== id)
        : [...enabledSections, id],
    );
  };

  const phase = roleIntelligence.phase;
  const canCheck =
    phase !== "loading" && roleIntelligence.targetRoleText.trim().length > 0;

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

      <section
        className="cv-role-intelligence"
        aria-label="Role Intelligence"
        aria-live="polite"
      >
        <div className="cv-role-intelligence__header">
          <div>
            <p className="cv-role-intelligence__eyebrow">Role intelligence</p>
            <h3>Canonical role hint</h3>
          </div>
          {phase !== "empty" && phase !== "ready" && (
            <span
              className={`cv-role-intelligence__chip cv-role-intelligence__chip--${
                phase === "accepted"
                  ? "accepted"
                  : phase === "unknown" || phase === "unavailable"
                    ? "unknown"
                    : phase === "kept_freeform"
                      ? "freeform"
                      : "suggested"
              }`}
            >
              {phase === "loading"
                ? "Checking"
                : phase === "accepted"
                  ? "Using suggested"
                  : phase === "kept_freeform"
                    ? "Using your wording"
                    : phase === "unknown"
                      ? "No match"
                      : phase === "unavailable"
                        ? "Unavailable"
                        : "Suggested"}
            </span>
          )}
        </div>
        <p className="cv-role-intelligence__advisory">
          Role intelligence is advisory. It never blocks save or export.
        </p>

        <Input
          label="Target role wording"
          value={roleIntelligence.targetRoleText}
          onChange={(e) => onRoleTextChange(e.target.value)}
          placeholder="e.g. Software Developer"
          fullWidth
        />

        {phase === "empty" && (
          <p className="cv-role-intelligence__body">
            Add a target role to check role intelligence.
          </p>
        )}
        {phase === "ready" && (
          <p className="cv-role-intelligence__body">
            Check for a deterministic suggested role match when you are ready.
          </p>
        )}
        {phase === "loading" && (
          <p className="cv-role-intelligence__body">Checking role match…</p>
        )}
        {phase === "suggested" && (
          <div className="cv-role-intelligence__result">
            <p className="cv-role-intelligence__result-label">Suggested role match</p>
            <p className="cv-role-intelligence__canonical">
              {roleIntelligence.matchedRoleTitle ||
                roleIntelligence.matchedRoleId ||
                "Suggested role"}
            </p>
            <p className="cv-role-intelligence__original">
              Your wording: <strong>{roleIntelligence.targetRoleText}</strong>
            </p>
            <div className="cv-role-intelligence__meta">
              <span>Source: {formatLabel(roleIntelligence.source)}</span>
              <span>Confidence: {formatLabel(roleIntelligence.confidence)}</span>
            </div>
            {roleIntelligence.explanation && (
              <p className="cv-role-intelligence__explain">{roleIntelligence.explanation}</p>
            )}
          </div>
        )}
        {phase === "unknown" && (
          <div className="cv-role-intelligence__result">
            <p className="cv-role-intelligence__result-label">No deterministic role match found</p>
            <p className="cv-role-intelligence__body">
              You can still continue with your own role wording.
            </p>
          </div>
        )}
        {phase === "accepted" && (
          <div className="cv-role-intelligence__result">
            <p className="cv-role-intelligence__result-label">Using suggested role</p>
            <p className="cv-role-intelligence__canonical">
              {roleIntelligence.matchedRoleTitle || roleIntelligence.matchedRoleId}
            </p>
            <div className="cv-role-intelligence__meta">
              <span>Source: {formatLabel(roleIntelligence.source)}</span>
              <span>Confidence: {formatLabel(roleIntelligence.confidence)}</span>
            </div>
          </div>
        )}
        {phase === "kept_freeform" && (
          <div className="cv-role-intelligence__result">
            <p className="cv-role-intelligence__result-label">Using your wording</p>
            <p className="cv-role-intelligence__original">
              <strong>{roleIntelligence.targetRoleText}</strong>
            </p>
          </div>
        )}
        {phase === "unavailable" && (
          <p className="cv-role-intelligence__body">
            Role intelligence is unavailable right now. You can continue without it.
          </p>
        )}

        <div className="cv-role-intelligence__actions">
          {phase === "loading" && (
            <Button variant="secondary" size="sm" loading disabled>
              Checking role match…
            </Button>
          )}
          {(phase === "empty" ||
            phase === "ready" ||
            phase === "suggested" ||
            phase === "unknown" ||
            phase === "unavailable") && (
            <Button
              variant="secondary"
              size="sm"
              disabled={!canCheck}
              onClick={onCheckRoleMatch}
            >
              Check role match
            </Button>
          )}
          {phase === "suggested" && (
            <>
              <Button variant="primary" size="sm" onClick={onAcceptSuggestedRole}>
                Use suggested role
              </Button>
              <Button variant="ghost" size="sm" onClick={onKeepFreeform}>
                Keep my wording
              </Button>
            </>
          )}
          {phase === "unknown" && (
            <Button variant="ghost" size="sm" onClick={onKeepFreeform}>
              Keep my wording
            </Button>
          )}
          {(phase === "accepted" || phase === "kept_freeform") && (
            <Button variant="ghost" size="sm" onClick={onRecheckRole}>
              Re-check
            </Button>
          )}
        </div>
      </section>

      <p className="cv-builder-studio-panel__footnote">
        Preview shows the full studio layout. PDF export maps this template to the
        <strong> {template.backendTemplate}</strong> style family until template-specific PDF
        rendering is expanded later.
      </p>
    </aside>
  );
}
