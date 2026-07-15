/**
 * PassportEditForms.tsx — Profile / Experience / Education editors (0052-F5).
 */

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from "lucide-react";
import { passportApi } from "@/lib/api";
import type {
  PassportEducationRead,
  PassportExperienceRead,
  PassportRead,
} from "@/types/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import {
  emptyToNull,
  getApiErrorMessage,
  isConflictError,
  joinCommaList,
  joinLines,
  looksLikeHttpUrl,
  normalizeDateInput,
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

export const PASSPORT_CONFLICT_MESSAGE = CONFLICT_COPY;
