/**
 * passportIntegrationUtils.ts — pure helpers for 0052-F7 Profile/CV/Roadmap
 * Passport read-only integration. No React. No network. No mutation.
 */

import type {
  PassportRead,
  PassportSeniorityLevel,
  PassportTargetRead,
} from "@/types/api";

export interface PassportTargetPrefill {
  id: string;
  label: string;
  target_role_text: string;
  target_country: string | null;
  target_region: string | null;
  target_seniority: PassportSeniorityLevel | null;
  time_horizon: string | null;
  priority: number;
}

const PASSPORT_TO_CV_SECTION: Record<string, string | null> = {
  profile: "summary",
  experience: "experience",
  education: "education",
  skills: "skills",
  projects: "projects",
  credentials: "certifications",
  targets: null,
};

function sectionEnabled(
  passport: PassportRead,
  section: string,
): boolean {
  const pref = passport.section_preferences.find((p) => p.section === section);
  return pref ? pref.enabled : true;
}

function profileHasContent(passport: PassportRead): boolean {
  const p = passport.profile;
  return Boolean(
    (p.professional_headline && p.professional_headline.trim()) ||
      (p.bio_summary && p.bio_summary.trim()) ||
      (passport.headline && passport.headline.trim()) ||
      (passport.summary && passport.summary.trim()) ||
      (p.interests && p.interests.length > 0) ||
      (p.phone && p.phone.trim()) ||
      (p.nationality && p.nationality.trim()),
  );
}

function sectionHasContent(passport: PassportRead, section: string): boolean {
  switch (section) {
    case "profile":
      return profileHasContent(passport);
    case "experience":
      return passport.experiences.length > 0;
    case "education":
      return passport.education.length > 0;
    case "projects":
      return passport.projects.length > 0;
    case "skills":
      return passport.skills.length > 0;
    case "credentials":
      return passport.credentials.length > 0;
    case "targets":
      return passport.targets.length > 0;
    default:
      return false;
  }
}

export function passportHasUsableProfile(
  passport: PassportRead | null | undefined,
): boolean {
  if (!passport) return false;
  return (
    profileHasContent(passport) ||
    passport.experiences.length > 0 ||
    passport.education.length > 0 ||
    passport.projects.length > 0 ||
    passport.skills.length > 0 ||
    passport.credentials.length > 0 ||
    passport.targets.length > 0
  );
}

export function passportSectionCounts(
  passport: PassportRead | null | undefined,
): Record<string, number> {
  if (!passport) {
    return {
      profile: 0,
      experience: 0,
      education: 0,
      projects: 0,
      skills: 0,
      credentials: 0,
      targets: 0,
    };
  }
  return {
    profile: profileHasContent(passport) ? 1 : 0,
    experience: passport.experiences.length,
    education: passport.education.length,
    projects: passport.projects.length,
    skills: passport.skills.length,
    credentials: passport.credentials.length,
    targets: passport.targets.length,
  };
}

export function passportEnabledCvSectionIds(
  passport: PassportRead | null | undefined,
): string[] {
  if (!passport) return [];
  const ids: string[] = [];
  for (const [passportSection, cvId] of Object.entries(PASSPORT_TO_CV_SECTION)) {
    if (!cvId) continue;
    if (!sectionEnabled(passport, passportSection)) continue;
    if (!sectionHasContent(passport, passportSection)) continue;
    if (!ids.includes(cvId)) ids.push(cvId);
  }
  return ids;
}

export function passportPrimaryTargetText(
  passport: PassportRead | null | undefined,
): string {
  if (!passport || passport.targets.length === 0) return "";
  const sorted = [...passport.targets].sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    return a.order_index - b.order_index;
  });
  return sorted[0]?.target_role_text?.trim() || "";
}

export function passportTargetsForPrefill(
  passport: PassportRead | null | undefined,
): PassportTargetPrefill[] {
  if (!passport) return [];
  return [...passport.targets]
    .sort((a, b) => {
      if (a.priority !== b.priority) return a.priority - b.priority;
      return a.order_index - b.order_index;
    })
    .map((t) => ({
      id: t.id,
      label: [
        t.target_role_text,
        t.target_country,
        t.target_seniority,
        `Priority ${t.priority}`,
      ]
        .filter(Boolean)
        .join(" · "),
      target_role_text: t.target_role_text,
      target_country: t.target_country,
      target_region: t.target_region,
      target_seniority: t.target_seniority,
      time_horizon: t.time_horizon,
      priority: t.priority,
    }));
}

export function buildRoadmapContextFromPassportTarget(
  target: PassportTargetRead | PassportTargetPrefill,
): string {
  const parts = [
    `Passport career target: ${target.target_role_text}`,
    target.target_country ? `Country: ${target.target_country}` : null,
    target.target_region ? `Region: ${target.target_region}` : null,
    target.target_seniority ? `Seniority: ${target.target_seniority}` : null,
    target.time_horizon ? `Time horizon: ${target.time_horizon}` : null,
    `Priority: ${target.priority}`,
  ].filter(Boolean);
  return parts.join(". ");
}

export function passportReadinessMessage(
  passport: PassportRead | null | undefined,
): string {
  if (!passport) {
    return "Career Passport is not available right now.";
  }
  if (!passportHasUsableProfile(passport)) {
    return "Your Passport is ready, but it does not have enough structured content yet.";
  }
  return "Career Passport available. Private and unverified. Use Passport sections for this CV.";
}
