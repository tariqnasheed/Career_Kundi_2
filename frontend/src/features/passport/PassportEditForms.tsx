/**
 * PassportEditForms.tsx — Passport section editors (0052-F5/F6).
 */

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from "lucide-react";
import { passportApi } from "@/lib/api";
import type {
  PassportCredentialRead,
  PassportCredentialType,
  PassportEducationRead,
  PassportExperienceRead,
  PassportProjectRead,
  PassportRead,
  PassportSeniorityLevel,
  PassportSkillRead,
  PassportTargetRead,
  TaxonomyPathwayType,
} from "@/types/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import {
  buildUnknownRoleTaxonomy,
  clampPriority,
  emptyToNull,
  getApiErrorMessage,
  isConflictError,
  joinCommaList,
  joinLines,
  looksLikeHttpUrl,
  normalizeDateInput,
  normalizeSelectValue,
  splitCommaList,
  splitLines,
  validateDateOrder,
} from "./passportFormUtils";
import styles from "./PassportEditForms.module.css";

export interface PassportEditorCallbacks {
  passport: PassportRead;
  onSaved: (next: PassportRead) => void;
  onConflict: () => void;
}

const CONFLICT_COPY =
  "Your Passport changed elsewhere. We refreshed the latest version. Please review and try again.";

type ProfileDraft = {
  professional_headline: string;
  bio_summary: string;
  phone: string;
  nationality: string;
  linkedin_url: string;
  github_url: string;
  portfolio_url: string;
  address_city: string;
  address_country: string;
  interests: string;
};

function profileDraftFromPassport(passport: PassportRead): ProfileDraft {
  const p = passport.profile;
  return {
    professional_headline: p.professional_headline ?? "",
    bio_summary: p.bio_summary ?? "",
    phone: p.phone ?? "",
    nationality: p.nationality ?? "",
    linkedin_url: p.linkedin_url ?? "",
    github_url: p.github_url ?? "",
    portfolio_url: p.portfolio_url ?? "",
    address_city: p.address_city ?? "",
    address_country: p.address_country ?? "",
    interests: joinCommaList(p.interests),
  };
}

export function PassportProfileEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<ProfileDraft>(() =>
    profileDraftFromPassport(passport),
  );
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (!open) {
      setDraft(profileDraftFromPassport(passport));
      setError(null);
    }
  }, [passport, open]);

  const onChange = (key: keyof ProfileDraft, value: string) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const baseline = profileDraftFromPassport(passport);
    const payload: Record<string, unknown> = {
      expected_version: passport.version,
    };

    const fields: (keyof ProfileDraft)[] = [
      "professional_headline",
      "bio_summary",
      "phone",
      "nationality",
      "linkedin_url",
      "github_url",
      "portfolio_url",
      "address_city",
      "address_country",
    ];

    for (const key of fields) {
      const next = emptyToNull(draft[key]);
      const prev = emptyToNull(baseline[key]);
      if (next !== prev) {
        if (
          (key === "linkedin_url" ||
            key === "github_url" ||
            key === "portfolio_url") &&
          !looksLikeHttpUrl(next)
        ) {
          setError("URLs must be blank or start with http:// or https://.");
          return;
        }
        payload[key] = next;
      }
    }

    const nextInterests = splitCommaList(draft.interests);
    const prevInterests = splitCommaList(baseline.interests);
    if (
      nextInterests.join("|").toLowerCase() !==
      prevInterests.join("|").toLowerCase()
    ) {
      payload.interests = nextInterests;
    }

    if (Object.keys(payload).length === 1) {
      setError("Change at least one field before saving.");
      return;
    }

    setPending(true);
    try {
      const next = await passportApi.patchProfile(
        payload as unknown as Parameters<typeof passportApi.patchProfile>[0],
      );
      onSaved(next);
      setOpen(false);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setOpen(false);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not update your Passport profile."),
      );
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          variant={open ? "secondary" : "primary"}
          leftIcon={<Pencil size={14} aria-hidden="true" />}
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
        >
          {open ? "Cancel profile edit" : "Edit profile"}
        </Button>
      </div>

      {open && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>Edit profile</CardTitle>
          </CardHeader>
          <CardContent>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Professional headline"
                value={draft.professional_headline}
                onChange={(e) => onChange("professional_headline", e.target.value)}
                fullWidth
              />
              <Textarea
                label="Summary"
                value={draft.bio_summary}
                onChange={(e) => onChange("bio_summary", e.target.value)}
                fullWidth
                rows={4}
              />
              <div className={styles.grid2}>
                <Input
                  label="Phone"
                  value={draft.phone}
                  onChange={(e) => onChange("phone", e.target.value)}
                  fullWidth
                />
                <Input
                  label="Nationality"
                  value={draft.nationality}
                  onChange={(e) => onChange("nationality", e.target.value)}
                  fullWidth
                />
              </div>
              <Input
                label="LinkedIn URL"
                value={draft.linkedin_url}
                onChange={(e) => onChange("linkedin_url", e.target.value)}
                fullWidth
              />
              <Input
                label="GitHub URL"
                value={draft.github_url}
                onChange={(e) => onChange("github_url", e.target.value)}
                fullWidth
              />
              <Input
                label="Portfolio URL"
                value={draft.portfolio_url}
                onChange={(e) => onChange("portfolio_url", e.target.value)}
                fullWidth
              />
              <div className={styles.grid2}>
                <Input
                  label="City"
                  value={draft.address_city}
                  onChange={(e) => onChange("address_city", e.target.value)}
                  fullWidth
                />
                <Input
                  label="Country"
                  value={draft.address_country}
                  onChange={(e) => onChange("address_country", e.target.value)}
                  fullWidth
                />
              </div>
              <Input
                label="Interests"
                hint="Comma-separated list"
                value={draft.interests}
                onChange={(e) => onChange("interests", e.target.value)}
                fullWidth
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save profile
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

type ExperienceDraft = {
  job_title: string;
  company_name: string;
  company_url: string;
  location: string;
  employment_type: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description_bullets: string;
};

function emptyExperienceDraft(): ExperienceDraft {
  return {
    job_title: "",
    company_name: "",
    company_url: "",
    location: "",
    employment_type: "",
    start_date: "",
    end_date: "",
    is_current: false,
    description_bullets: "",
  };
}

function experienceDraftFromEntry(entry: PassportExperienceRead): ExperienceDraft {
  return {
    job_title: entry.job_title,
    company_name: entry.company_name,
    company_url: entry.company_url ?? "",
    location: entry.location ?? "",
    employment_type: entry.employment_type ?? "",
    start_date: normalizeDateInput(entry.start_date),
    end_date: normalizeDateInput(entry.end_date),
    is_current: entry.is_current,
    description_bullets: joinLines(entry.description_bullets),
  };
}

function sortedExperiences(passport: PassportRead): PassportExperienceRead[] {
  return [...passport.experiences].sort((a, b) => a.order_index - b.order_index);
}

export function PassportExperienceEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedExperiences(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ExperienceDraft>(emptyExperienceDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptyExperienceDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptyExperienceDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportExperienceRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(experienceDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const jobTitle = emptyToNull(draft.job_title);
    const companyName = emptyToNull(draft.company_name);
    if (!jobTitle) {
      setError("Job title is required.");
      return;
    }
    if (!companyName) {
      setError("Company name is required.");
      return;
    }

    const startDate = emptyToNull(draft.start_date);
    const endDate = draft.is_current ? null : emptyToNull(draft.end_date);
    const dateError = validateDateOrder(startDate, endDate, draft.is_current);
    if (dateError) {
      setError(dateError);
      return;
    }

    const companyUrl = emptyToNull(draft.company_url);
    if (!looksLikeHttpUrl(companyUrl)) {
      setError("Company URL must be blank or start with http:// or https://.");
      return;
    }

    setPending(true);
    try {
      let next: PassportRead;
      if (mode === "add") {
        next = await passportApi.createExperience({
          expected_version: passport.version,
          job_title: jobTitle,
          company_name: companyName,
          company_url: companyUrl,
          location: emptyToNull(draft.location),
          employment_type: emptyToNull(draft.employment_type),
          start_date: startDate,
          end_date: endDate,
          is_current: draft.is_current,
          description_bullets: splitLines(draft.description_bullets),
        });
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchExperience(editingId, {
          expected_version: passport.version,
          job_title: jobTitle,
          company_name: companyName,
          company_url: companyUrl,
          location: emptyToNull(draft.location),
          employment_type: emptyToNull(draft.employment_type),
          start_date: startDate,
          end_date: endDate,
          is_current: draft.is_current,
          description_bullets: splitLines(draft.description_bullets),
        });
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not save this experience entry."),
      );
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteExperience(
        entryId,
        passport.version,
      );
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not delete this experience entry."),
      );
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderExperiences({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not reorder experience entries."),
      );
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add experience
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.job_title}</p>
              <p className={styles.entryMeta}>
                {entry.company_name}
                {entry.location ? ` · ${entry.location}` : ""}
                {entry.is_current ? " · Current" : ""}
              </p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.job_title} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.job_title} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>Delete this experience?</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    loading={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() => setConfirmDeleteId(null)}
                    disabled={pending}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  onClick={() => setConfirmDeleteId(entry.id)}
                  disabled={pending}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {(mode === "add" || mode === "edit") && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>
              {mode === "add" ? "Add experience" : "Edit experience"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Job title"
                value={draft.job_title}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, job_title: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Company name"
                value={draft.company_name}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, company_name: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Company URL"
                value={draft.company_url}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, company_url: e.target.value }))
                }
                fullWidth
              />
              <div className={styles.grid2}>
                <Input
                  label="Location"
                  value={draft.location}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, location: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="Employment type"
                  value={draft.employment_type}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, employment_type: e.target.value }))
                  }
                  fullWidth
                />
              </div>
              <div className={styles.grid2}>
                <Input
                  label="Start date"
                  type="date"
                  value={draft.start_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, start_date: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="End date"
                  type="date"
                  value={draft.end_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, end_date: e.target.value }))
                  }
                  disabled={draft.is_current}
                  fullWidth
                />
              </div>
              <label className={styles.checkLabel}>
                <input
                  type="checkbox"
                  checked={draft.is_current}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      is_current: e.target.checked,
                      end_date: e.target.checked ? "" : d.end_date,
                    }))
                  }
                />
                This is my current role
              </label>
              <Textarea
                label="Description bullets"
                hint="One bullet per line"
                value={draft.description_bullets}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    description_bullets: e.target.value,
                  }))
                }
                fullWidth
                rows={4}
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save experience
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

type EducationDraft = {
  degree: string;
  field_of_study: string;
  institution: string;
  location: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  grade: string;
  description_bullets: string;
  relevant_coursework: string;
};

function emptyEducationDraft(): EducationDraft {
  return {
    degree: "",
    field_of_study: "",
    institution: "",
    location: "",
    start_date: "",
    end_date: "",
    is_current: false,
    grade: "",
    description_bullets: "",
    relevant_coursework: "",
  };
}

function educationDraftFromEntry(entry: PassportEducationRead): EducationDraft {
  return {
    degree: entry.degree,
    field_of_study: entry.field_of_study ?? "",
    institution: entry.institution,
    location: entry.location ?? "",
    start_date: normalizeDateInput(entry.start_date),
    end_date: normalizeDateInput(entry.end_date),
    is_current: entry.is_current,
    grade: entry.grade ?? "",
    description_bullets: joinLines(entry.description_bullets),
    relevant_coursework: joinLines(entry.relevant_coursework),
  };
}

function sortedEducation(passport: PassportRead): PassportEducationRead[] {
  return [...passport.education].sort((a, b) => a.order_index - b.order_index);
}

export function PassportEducationEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedEducation(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<EducationDraft>(emptyEducationDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptyEducationDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptyEducationDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportEducationRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(educationDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const degree = emptyToNull(draft.degree);
    const institution = emptyToNull(draft.institution);
    if (!degree) {
      setError("Degree is required.");
      return;
    }
    if (!institution) {
      setError("Institution is required.");
      return;
    }

    const startDate = emptyToNull(draft.start_date);
    const endDate = draft.is_current ? null : emptyToNull(draft.end_date);
    const dateError = validateDateOrder(startDate, endDate, draft.is_current);
    if (dateError) {
      setError(dateError);
      return;
    }

    setPending(true);
    try {
      let next: PassportRead;
      if (mode === "add") {
        next = await passportApi.createEducation({
          expected_version: passport.version,
          degree,
          institution,
          field_of_study: emptyToNull(draft.field_of_study),
          location: emptyToNull(draft.location),
          start_date: startDate,
          end_date: endDate,
          is_current: draft.is_current,
          grade: emptyToNull(draft.grade),
          description_bullets: splitLines(draft.description_bullets),
          relevant_coursework: splitLines(draft.relevant_coursework),
        });
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchEducation(editingId, {
          expected_version: passport.version,
          degree,
          institution,
          field_of_study: emptyToNull(draft.field_of_study),
          location: emptyToNull(draft.location),
          start_date: startDate,
          end_date: endDate,
          is_current: draft.is_current,
          grade: emptyToNull(draft.grade),
          description_bullets: splitLines(draft.description_bullets),
          relevant_coursework: splitLines(draft.relevant_coursework),
        });
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not save this education entry."),
      );
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteEducation(entryId, passport.version);
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not delete this education entry."),
      );
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderEducation({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(
        getApiErrorMessage(err, "Could not reorder education entries."),
      );
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add education
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.degree}</p>
              <p className={styles.entryMeta}>
                {entry.institution}
                {entry.field_of_study ? ` · ${entry.field_of_study}` : ""}
                {entry.is_current ? " · Current" : ""}
              </p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.degree} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.degree} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>Delete this education?</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    loading={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={() => setConfirmDeleteId(null)}
                    disabled={pending}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  onClick={() => setConfirmDeleteId(entry.id)}
                  disabled={pending}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {(mode === "add" || mode === "edit") && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>
              {mode === "add" ? "Add education" : "Edit education"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Degree"
                value={draft.degree}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, degree: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Institution"
                value={draft.institution}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, institution: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Field of study"
                value={draft.field_of_study}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, field_of_study: e.target.value }))
                }
                fullWidth
              />
              <div className={styles.grid2}>
                <Input
                  label="Location"
                  value={draft.location}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, location: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="Grade"
                  value={draft.grade}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, grade: e.target.value }))
                  }
                  fullWidth
                />
              </div>
              <div className={styles.grid2}>
                <Input
                  label="Start date"
                  type="date"
                  value={draft.start_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, start_date: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="End date"
                  type="date"
                  value={draft.end_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, end_date: e.target.value }))
                  }
                  disabled={draft.is_current}
                  fullWidth
                />
              </div>
              <label className={styles.checkLabel}>
                <input
                  type="checkbox"
                  checked={draft.is_current}
                  onChange={(e) =>
                    setDraft((d) => ({
                      ...d,
                      is_current: e.target.checked,
                      end_date: e.target.checked ? "" : d.end_date,
                    }))
                  }
                />
                I am currently studying here
              </label>
              <Textarea
                label="Description bullets"
                hint="One bullet per line"
                value={draft.description_bullets}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    description_bullets: e.target.value,
                  }))
                }
                fullWidth
                rows={3}
              />
              <Textarea
                label="Relevant coursework"
                hint="One course per line"
                value={draft.relevant_coursework}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    relevant_coursework: e.target.value,
                  }))
                }
                fullWidth
                rows={3}
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save education
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}


// ---------------------------------------------------------------------------
// 0052-F6 — Projects / Skills / Credentials / Targets
// ---------------------------------------------------------------------------

const SKILL_TYPES = [
  "technical",
  "soft",
  "tool",
  "domain",
  "language",
  "other",
] as const;

const PROFICIENCY_OPTIONS = [
  "",
  "beginner",
  "intermediate",
  "advanced",
  "expert",
] as const;

const CREDENTIAL_TYPES: PassportCredentialType[] = [
  "certification",
  "license",
  "course_certificate",
  "education_award",
  "professional_membership",
  "other",
];

const PATHWAY_OPTIONS: Array<TaxonomyPathwayType | ""> = [
  "",
  "skill_gap",
  "career_switch",
  "graduate_launch",
  "interview_preparation",
  "job_application",
  "study_education",
  "professional_certification",
  "public_sector",
  "regional_readiness",
  "portfolio_project",
  "promotion_growth",
];

const SENIORITY_OPTIONS: Array<PassportSeniorityLevel | ""> = [
  "",
  "entry",
  "junior",
  "mid",
  "senior",
  "lead",
  "principal",
  "manager",
  "director",
  "executive",
  "unknown",
];

function SelectField({
  id,
  label,
  value,
  onChange,
  options,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <div className={styles.selectWrap}>
      <label className={styles.fieldLabel} htmlFor={id}>
        {label}
      </label>
      <select
        id={id}
        className={styles.selectField}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {options.map((opt) => (
          <option key={opt.value || "__blank"} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

type ProjectDraft = {
  title: string;
  description: string;
  technologies: string;
  project_url: string;
  start_date: string;
  end_date: string;
  role: string;
  key_achievements: string;
};

function emptyProjectDraft(): ProjectDraft {
  return {
    title: "",
    description: "",
    technologies: "",
    project_url: "",
    start_date: "",
    end_date: "",
    role: "",
    key_achievements: "",
  };
}

function projectDraftFromEntry(entry: PassportProjectRead): ProjectDraft {
  return {
    title: entry.title,
    description: entry.description ?? "",
    technologies: joinCommaList(entry.technologies),
    project_url: entry.project_url ?? "",
    start_date: normalizeDateInput(entry.start_date),
    end_date: normalizeDateInput(entry.end_date),
    role: entry.role ?? "",
    key_achievements: joinLines(entry.key_achievements),
  };
}

function sortedProjects(passport: PassportRead): PassportProjectRead[] {
  return [...passport.projects].sort((a, b) => a.order_index - b.order_index);
}

export function PassportProjectEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedProjects(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ProjectDraft>(emptyProjectDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptyProjectDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptyProjectDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportProjectRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(projectDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    const title = emptyToNull(draft.title);
    if (!title) {
      setError("Title is required.");
      return;
    }
    const startDate = emptyToNull(draft.start_date);
    const endDate = emptyToNull(draft.end_date);
    const dateError = validateDateOrder(startDate, endDate, false);
    if (dateError) {
      setError(dateError);
      return;
    }
    const projectUrl = emptyToNull(draft.project_url);
    if (!looksLikeHttpUrl(projectUrl)) {
      setError("Project URL must be blank or start with http:// or https://.");
      return;
    }
    setPending(true);
    try {
      let next: PassportRead;
      const payloadBase = {
        expected_version: passport.version,
        title,
        description: emptyToNull(draft.description),
        technologies: splitCommaList(draft.technologies),
        project_url: projectUrl,
        start_date: startDate,
        end_date: endDate,
        role: emptyToNull(draft.role),
        key_achievements: splitLines(draft.key_achievements),
      };
      if (mode === "add") {
        next = await passportApi.createProject(payloadBase);
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchProject(editingId, payloadBase);
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not save this project."));
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteProject(entryId, passport.version);
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not delete this project."));
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderProjects({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not reorder projects."));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add project
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.title}</p>
              <p className={styles.entryMeta}>
                {[entry.role, entry.technologies.slice(0, 3).join(", ")]
                  .filter(Boolean)
                  .join(" · ") || "Self-declared project"}
              </p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.title} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.title} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>Delete this project?</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    disabled={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  disabled={pending}
                  onClick={() => setConfirmDeleteId(entry.id)}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {mode !== "idle" && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>{mode === "add" ? "Add project" : "Edit project"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Title"
                value={draft.title}
                onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
                fullWidth
              />
              <Textarea
                label="Description"
                value={draft.description}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, description: e.target.value }))
                }
                fullWidth
                rows={3}
              />
              <Input
                label="Technologies"
                hint="Comma-separated list"
                value={draft.technologies}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, technologies: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Project URL"
                value={draft.project_url}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, project_url: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Role"
                value={draft.role}
                onChange={(e) => setDraft((d) => ({ ...d, role: e.target.value }))}
                fullWidth
              />
              <div className={styles.grid2}>
                <Input
                  label="Start date"
                  type="date"
                  value={draft.start_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, start_date: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="End date"
                  type="date"
                  value={draft.end_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, end_date: e.target.value }))
                  }
                  fullWidth
                />
              </div>
              <Textarea
                label="Key achievements"
                hint="One achievement per line"
                value={draft.key_achievements}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, key_achievements: e.target.value }))
                }
                fullWidth
                rows={3}
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save project
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

type SkillDraft = {
  name: string;
  skill_type: string;
  category: string;
  proficiency: string;
};

function emptySkillDraft(): SkillDraft {
  return {
    name: "",
    skill_type: "technical",
    category: "",
    proficiency: "",
  };
}

function skillDraftFromEntry(entry: PassportSkillRead): SkillDraft {
  return {
    name: entry.name,
    skill_type: entry.skill_type || "technical",
    category: entry.category ?? "",
    proficiency: entry.proficiency ?? "",
  };
}

function sortedSkills(passport: PassportRead): PassportSkillRead[] {
  return [...passport.skills].sort((a, b) => a.order_index - b.order_index);
}

export function PassportSkillEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedSkills(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<SkillDraft>(emptySkillDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptySkillDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptySkillDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportSkillRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(skillDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    const name = emptyToNull(draft.name);
    const skillType = emptyToNull(draft.skill_type);
    if (!name) {
      setError("Skill name is required.");
      return;
    }
    if (!skillType) {
      setError("Skill type is required.");
      return;
    }
    setPending(true);
    try {
      let next: PassportRead;
      const payloadBase = {
        expected_version: passport.version,
        name,
        skill_type: skillType,
        category: emptyToNull(draft.category),
        proficiency: normalizeSelectValue(draft.proficiency),
      };
      if (mode === "add") {
        next = await passportApi.createSkill(payloadBase);
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchSkill(editingId, payloadBase);
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not save this skill."));
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteSkill(entryId, passport.version);
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not delete this skill."));
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderSkills({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not reorder skills."));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add skill
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.name}</p>
              <p className={styles.entryMeta}>
                {[entry.skill_type, entry.category, entry.proficiency]
                  .filter(Boolean)
                  .join(" · ") || "Self-declared skill"}
              </p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.name} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.name} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>Delete this skill?</span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    disabled={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  disabled={pending}
                  onClick={() => setConfirmDeleteId(entry.id)}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {mode !== "idle" && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>{mode === "add" ? "Add skill" : "Edit skill"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Name"
                value={draft.name}
                onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                fullWidth
              />
              <SelectField
                id="skill-type"
                label="Skill type"
                value={draft.skill_type}
                onChange={(value) => setDraft((d) => ({ ...d, skill_type: value }))}
                options={SKILL_TYPES.map((t) => ({ value: t, label: t }))}
              />
              <Input
                label="Category"
                value={draft.category}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, category: e.target.value }))
                }
                fullWidth
              />
              <SelectField
                id="skill-proficiency"
                label="Proficiency"
                value={draft.proficiency}
                onChange={(value) =>
                  setDraft((d) => ({ ...d, proficiency: value }))
                }
                options={[
                  { value: "", label: "Not specified" },
                  ...PROFICIENCY_OPTIONS.filter(Boolean).map((p) => ({
                    value: p,
                    label: p,
                  })),
                ]}
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save skill
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

type CredentialDraft = {
  credential_type: PassportCredentialType;
  name: string;
  issuing_organization: string;
  issue_date: string;
  expiry_date: string;
  credential_id: string;
  credential_url: string;
};

function emptyCredentialDraft(): CredentialDraft {
  return {
    credential_type: "certification",
    name: "",
    issuing_organization: "",
    issue_date: "",
    expiry_date: "",
    credential_id: "",
    credential_url: "",
  };
}

function credentialDraftFromEntry(entry: PassportCredentialRead): CredentialDraft {
  return {
    credential_type: entry.credential_type,
    name: entry.name,
    issuing_organization: entry.issuing_organization,
    issue_date: normalizeDateInput(entry.issue_date),
    expiry_date: normalizeDateInput(entry.expiry_date),
    credential_id: entry.credential_id ?? "",
    credential_url: entry.credential_url ?? "",
  };
}

function sortedCredentials(passport: PassportRead): PassportCredentialRead[] {
  return [...passport.credentials].sort((a, b) => a.order_index - b.order_index);
}

export function PassportCredentialEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedCredentials(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<CredentialDraft>(emptyCredentialDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptyCredentialDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptyCredentialDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportCredentialRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(credentialDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    const name = emptyToNull(draft.name);
    const org = emptyToNull(draft.issuing_organization);
    if (!name) {
      setError("Credential name is required.");
      return;
    }
    if (!org) {
      setError("Issuing organization is required.");
      return;
    }
    const issueDate = emptyToNull(draft.issue_date);
    const expiryDate = emptyToNull(draft.expiry_date);
    if (issueDate && expiryDate && expiryDate < issueDate) {
      setError("Expiry date must be on or after the issue date.");
      return;
    }
    const credentialUrl = emptyToNull(draft.credential_url);
    if (!looksLikeHttpUrl(credentialUrl)) {
      setError("Credential URL must be blank or start with http:// or https://.");
      return;
    }
    setPending(true);
    try {
      let next: PassportRead;
      const payloadBase = {
        expected_version: passport.version,
        credential_type: draft.credential_type,
        name,
        issuing_organization: org,
        issue_date: issueDate,
        expiry_date: expiryDate,
        credential_id: emptyToNull(draft.credential_id),
        credential_url: credentialUrl,
      };
      if (mode === "add") {
        next = await passportApi.createCredential(payloadBase);
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchCredential(editingId, payloadBase);
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not save this credential."));
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteCredential(entryId, passport.version);
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not delete this credential."));
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderCredentials({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not reorder credentials."));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <p className={styles.truthNote}>
        Credential reference · Not independently verified
      </p>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add credential
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.name}</p>
              <p className={styles.entryMeta}>
                {entry.issuing_organization}
                {entry.credential_type ? ` · ${entry.credential_type}` : ""}
              </p>
              <p className={styles.truthNote}>
                Credential reference · Not independently verified
              </p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.name} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.name} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>
                    Delete this credential?
                  </span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    disabled={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  disabled={pending}
                  onClick={() => setConfirmDeleteId(entry.id)}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {mode !== "idle" && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>
              {mode === "add" ? "Add credential" : "Edit credential"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={styles.truthNote}>
              Credential reference · Not independently verified
            </p>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <SelectField
                id="credential-type"
                label="Credential type"
                value={draft.credential_type}
                onChange={(value) =>
                  setDraft((d) => ({
                    ...d,
                    credential_type: value as PassportCredentialType,
                  }))
                }
                options={CREDENTIAL_TYPES.map((t) => ({ value: t, label: t }))}
              />
              <Input
                label="Name"
                value={draft.name}
                onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                fullWidth
              />
              <Input
                label="Issuing organization"
                value={draft.issuing_organization}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    issuing_organization: e.target.value,
                  }))
                }
                fullWidth
              />
              <div className={styles.grid2}>
                <Input
                  label="Issue date"
                  type="date"
                  value={draft.issue_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, issue_date: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="Expiry date"
                  type="date"
                  value={draft.expiry_date}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, expiry_date: e.target.value }))
                  }
                  fullWidth
                />
              </div>
              <Input
                label="Credential ID"
                value={draft.credential_id}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, credential_id: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Credential URL"
                value={draft.credential_url}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, credential_url: e.target.value }))
                }
                fullWidth
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save credential
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

type TargetDraft = {
  target_role_text: string;
  pathway_type: string;
  target_country: string;
  target_region: string;
  target_industry: string;
  target_seniority: string;
  time_horizon: string;
  priority: string;
  role_taxonomy_text: string;
};

function emptyTargetDraft(): TargetDraft {
  return {
    target_role_text: "",
    pathway_type: "",
    target_country: "",
    target_region: "",
    target_industry: "",
    target_seniority: "",
    time_horizon: "",
    priority: "3",
    role_taxonomy_text: "",
  };
}

function targetDraftFromEntry(entry: PassportTargetRead): TargetDraft {
  return {
    target_role_text: entry.target_role_text,
    pathway_type: entry.pathway_type ?? "",
    target_country: entry.target_country ?? "",
    target_region: entry.target_region ?? "",
    target_industry: entry.target_industry ?? "",
    target_seniority: entry.target_seniority ?? "",
    time_horizon: entry.time_horizon ?? "",
    priority: String(entry.priority ?? 3),
    role_taxonomy_text: entry.role_taxonomy?.input_text ?? "",
  };
}

function sortedTargets(passport: PassportRead): PassportTargetRead[] {
  return [...passport.targets].sort((a, b) => a.order_index - b.order_index);
}

export function PassportTargetEditor({
  passport,
  onSaved,
  onConflict,
}: PassportEditorCallbacks) {
  const entries = useMemo(() => sortedTargets(passport), [passport]);
  const [mode, setMode] = useState<"idle" | "add" | "edit">("idle");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<TargetDraft>(emptyTargetDraft);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const resetForm = () => {
    setMode("idle");
    setEditingId(null);
    setDraft(emptyTargetDraft());
    setError(null);
  };

  const openAdd = () => {
    setMode("add");
    setEditingId(null);
    setDraft(emptyTargetDraft());
    setError(null);
    setConfirmDeleteId(null);
  };

  const openEdit = (entry: PassportTargetRead) => {
    setMode("edit");
    setEditingId(entry.id);
    setDraft(targetDraftFromEntry(entry));
    setError(null);
    setConfirmDeleteId(null);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    const roleText = emptyToNull(draft.target_role_text);
    if (!roleText) {
      setError("Target role is required.");
      return;
    }
    const priority = clampPriority(draft.priority);
    const pathway = normalizeSelectValue(draft.pathway_type) as
      | TaxonomyPathwayType
      | null;
    const seniority = normalizeSelectValue(draft.target_seniority) as
      | PassportSeniorityLevel
      | null;
    setPending(true);
    try {
      let next: PassportRead;
      const payloadBase = {
        expected_version: passport.version,
        target_role_text: roleText,
        role_taxonomy: buildUnknownRoleTaxonomy(draft.role_taxonomy_text),
        pathway_type: pathway,
        target_country: emptyToNull(draft.target_country),
        target_region: emptyToNull(draft.target_region),
        target_industry: emptyToNull(draft.target_industry),
        target_seniority: seniority,
        time_horizon: emptyToNull(draft.time_horizon),
        priority,
      };
      if (mode === "add") {
        next = await passportApi.createTarget(payloadBase);
      } else if (mode === "edit" && editingId) {
        next = await passportApi.patchTarget(editingId, payloadBase);
      } else {
        setPending(false);
        return;
      }
      onSaved(next);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        resetForm();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not save this career target."));
    } finally {
      setPending(false);
    }
  };

  const handleDelete = async (entryId: string) => {
    setError(null);
    setPending(true);
    try {
      const next = await passportApi.deleteTarget(entryId, passport.version);
      onSaved(next);
      setConfirmDeleteId(null);
      resetForm();
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not delete this career target."));
    } finally {
      setPending(false);
    }
  };

  const move = async (entryId: string, direction: -1 | 1) => {
    const ids = entries.map((e) => e.id);
    const index = ids.indexOf(entryId);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= ids.length) return;
    const ordered = [...ids];
    const [item] = ordered.splice(index, 1);
    ordered.splice(target, 0, item);
    setPending(true);
    setError(null);
    try {
      const next = await passportApi.reorderTargets({
        expected_version: passport.version,
        ordered_ids: ordered,
      });
      onSaved(next);
    } catch (err) {
      if (isConflictError(err)) {
        onConflict();
        setConfirmDeleteId(null);
        return;
      }
      setError(getApiErrorMessage(err, "Could not reorder career targets."));
    } finally {
      setPending(false);
    }
  };

  return (
    <div className={styles.editorBlock}>
      <p className={styles.truthNote}>Career target · Not a Roadmap yet</p>
      <div className={styles.editorToolbar}>
        <Button
          type="button"
          size="sm"
          leftIcon={<Plus size={14} aria-hidden="true" />}
          onClick={openAdd}
          disabled={pending || mode === "add"}
        >
          Add target
        </Button>
      </div>

      <ul className={styles.entryList}>
        {entries.map((entry, index) => (
          <li key={entry.id} className={styles.entryItem}>
            <div className={styles.entryMain}>
              <p className={styles.entryTitle}>{entry.target_role_text}</p>
              <p className={styles.entryMeta}>
                {[
                  entry.target_country,
                  entry.target_region,
                  entry.target_seniority,
                  entry.time_horizon,
                  `Priority ${entry.priority}`,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              <p className={styles.truthNote}>Career target · Not a Roadmap yet</p>
            </div>
            <div className={styles.entryActions}>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.target_role_text} up`}
                disabled={pending || index === 0}
                onClick={() => void move(entry.id, -1)}
                leftIcon={<ArrowUp size={14} aria-hidden="true" />}
              >
                Up
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                aria-label={`Move ${entry.target_role_text} down`}
                disabled={pending || index === entries.length - 1}
                onClick={() => void move(entry.id, 1)}
                leftIcon={<ArrowDown size={14} aria-hidden="true" />}
              >
                Down
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => openEdit(entry)}
                disabled={pending}
              >
                Edit
              </Button>
              {confirmDeleteId === entry.id ? (
                <div className={styles.confirmRow}>
                  <span className={styles.confirmText}>
                    Delete this career target?
                  </span>
                  <Button
                    type="button"
                    size="sm"
                    variant="danger"
                    disabled={pending}
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Confirm delete
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  leftIcon={<Trash2 size={14} aria-hidden="true" />}
                  disabled={pending}
                  onClick={() => setConfirmDeleteId(entry.id)}
                >
                  Delete
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {mode !== "idle" && (
        <Card className={styles.formCard}>
          <CardHeader>
            <CardTitle>
              {mode === "add" ? "Add career target" : "Edit career target"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className={styles.truthNote}>Career target · Not a Roadmap yet</p>
            <form className={styles.form} onSubmit={(e) => void handleSubmit(e)}>
              <Input
                label="Target role"
                value={draft.target_role_text}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, target_role_text: e.target.value }))
                }
                fullWidth
              />
              <SelectField
                id="target-pathway"
                label="Pathway type"
                value={draft.pathway_type}
                onChange={(value) =>
                  setDraft((d) => ({ ...d, pathway_type: value }))
                }
                options={PATHWAY_OPTIONS.map((p) => ({
                  value: p,
                  label: p || "Not specified",
                }))}
              />
              <div className={styles.grid2}>
                <Input
                  label="Target country"
                  value={draft.target_country}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, target_country: e.target.value }))
                  }
                  fullWidth
                />
                <Input
                  label="Target region"
                  value={draft.target_region}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, target_region: e.target.value }))
                  }
                  fullWidth
                />
              </div>
              <Input
                label="Target industry"
                value={draft.target_industry}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, target_industry: e.target.value }))
                }
                fullWidth
              />
              <SelectField
                id="target-seniority"
                label="Target seniority"
                value={draft.target_seniority}
                onChange={(value) =>
                  setDraft((d) => ({ ...d, target_seniority: value }))
                }
                options={SENIORITY_OPTIONS.map((s) => ({
                  value: s,
                  label: s || "Not specified",
                }))}
              />
              <Input
                label="Time horizon"
                value={draft.time_horizon}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, time_horizon: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Priority"
                type="number"
                hint="1 (highest) to 5 (lowest interest). Values outside 1–5 are adjusted."
                value={draft.priority}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, priority: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Role taxonomy text"
                hint="Optional advisory note only. Does not look up taxonomy."
                value={draft.role_taxonomy_text}
                onChange={(e) =>
                  setDraft((d) => ({
                    ...d,
                    role_taxonomy_text: e.target.value,
                  }))
                }
                fullWidth
              />
              {error && (
                <p className={styles.formError} role="alert">
                  {error}
                </p>
              )}
              <div className={styles.formActions}>
                <Button type="submit" size="sm" loading={pending} disabled={pending}>
                  Save target
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={resetForm}
                  disabled={pending}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {error && mode === "idle" && (
        <p className={styles.formError} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export const PASSPORT_CONFLICT_MESSAGE = CONFLICT_COPY;
