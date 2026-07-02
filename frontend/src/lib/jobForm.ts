/**
 * Helpers to convert between SavedJob API objects and the editable job form.
 */

import type { ExtractedSkill, SavedJobRead } from "../types/api";

export interface JobFormState {
  title: string;
  company_name: string;
  company_url: string;
  location: string;
  employment_type: string;
  experience_level: string;
  is_remote: boolean;
  salary_min: string;
  salary_max: string;
  salary_currency: string;
  source_url: string;
  description_raw: string;
  responsibilities: string;
  requirements: string;
  benefits: string;
  skills: string;
}

export const EMPTY_JOB_FORM: JobFormState = {
  title: "",
  company_name: "",
  company_url: "",
  location: "",
  employment_type: "",
  experience_level: "",
  is_remote: false,
  salary_min: "",
  salary_max: "",
  salary_currency: "GBP",
  source_url: "",
  description_raw: "",
  responsibilities: "",
  requirements: "",
  benefits: "",
  skills: "",
};

function linesToList(text: string): string[] {
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}

function listToLines(items: string[] | undefined): string {
  return (items ?? []).join("\n");
}

function skillsToText(skills: ExtractedSkill[] | undefined): string {
  return (skills ?? []).map((s) => s.skill).filter(Boolean).join(", ");
}

function textToSkills(text: string): ExtractedSkill[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((skill) => ({ skill, category: "technical" as const, importance: "medium" as const }));
}

export function jobToForm(job: SavedJobRead): JobFormState {
  const reqs = job.requirements ?? [];
  const expLine = reqs.find((r) => /^experience:/i.test(r));
  const otherReqs = expLine ? reqs.filter((r) => r !== expLine) : reqs;
  const expMatch = expLine?.match(/^experience:\s*(.+)/i);

  return {
    title: job.title ?? "",
    company_name: job.company_name ?? "",
    company_url: job.company_url ?? "",
    location: job.location ?? "",
    employment_type: job.employment_type ?? "",
    experience_level: expMatch?.[1] ?? "",
    is_remote: job.is_remote ?? false,
    salary_min: job.salary_min != null ? String(job.salary_min) : "",
    salary_max: job.salary_max != null ? String(job.salary_max) : "",
    salary_currency: job.salary_currency ?? "GBP",
    source_url: job.source_url ?? "",
    description_raw: job.description_raw ?? "",
    responsibilities: listToLines(job.responsibilities),
    requirements: listToLines(otherReqs),
    benefits: listToLines(job.benefits),
    skills: skillsToText(job.extracted_skills),
  };
}

export function formToSavePayload(form: JobFormState): Record<string, unknown> {
  const requirements = linesToList(form.requirements);
  if (form.experience_level.trim()) {
    requirements.unshift(`Experience: ${form.experience_level.trim()}`);
  }

  return {
    title: form.title.trim() || "Untitled Role",
    company_name: form.company_name.trim() || null,
    company_url: form.company_url.trim() || null,
    location: form.location.trim() || null,
    employment_type: form.employment_type.trim() || null,
    is_remote: form.is_remote,
    salary_min: form.salary_min ? Number(form.salary_min) : null,
    salary_max: form.salary_max ? Number(form.salary_max) : null,
    salary_currency: form.salary_currency.trim() || null,
    source_url: form.source_url.trim() || null,
    description_raw: form.description_raw.trim() || null,
    responsibilities: linesToList(form.responsibilities),
    requirements,
    benefits: linesToList(form.benefits),
    extracted_skills: textToSkills(form.skills),
    import_method: "manual",
  };
}
