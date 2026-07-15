/**
 * passportIntegrationUtils.test.ts — 0052-F7
 */

import { describe, it, expect } from "vitest";
import type { PassportRead } from "@/types/api";
import {
  buildRoadmapContextFromPassportTarget,
  passportEnabledCvSectionIds,
  passportHasUsableProfile,
  passportPrimaryTargetText,
  passportReadinessMessage,
  passportSectionCounts,
  passportTargetsForPrefill,
} from "./passportIntegrationUtils";

const META = {
  source_status: "user_asserted",
  support_status: "profile_supported" as const,
  verification_status: "unverified" as const,
};

function emptyPassport(overrides: Partial<PassportRead> = {}): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada",
    headline: null,
    summary: null,
    visibility: "private",
    version: 1,
    section_preferences: [
      { section: "profile", order_index: 0, enabled: true },
      { section: "experience", order_index: 1, enabled: true },
      { section: "education", order_index: 2, enabled: true },
      { section: "projects", order_index: 3, enabled: true },
      { section: "skills", order_index: 4, enabled: true },
      { section: "credentials", order_index: 5, enabled: true },
      { section: "targets", order_index: 6, enabled: true },
    ],
    profile: {
      phone: null,
      date_of_birth: null,
      nationality: null,
      linkedin_url: null,
      github_url: null,
      portfolio_url: null,
      twitter_url: null,
      other_social_links: [],
      address_city: null,
      address_state: null,
      address_country: null,
      photo_url: null,
      professional_headline: null,
      bio_summary: null,
      declaration_text: null,
      references_available_on_request: false,
      interests: [],
      record_meta: { ...META },
    },
    experiences: [],
    education: [],
    projects: [],
    skills: [],
    credentials: [],
    targets: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function populatedPassport(): PassportRead {
  return emptyPassport({
    version: 3,
    headline: "Engineer",
    profile: {
      ...emptyPassport().profile,
      professional_headline: "Engineer",
      bio_summary: "Builds careful systems.",
    },
    experiences: [
      {
        id: "e1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        job_title: "Engineer",
        company_name: "Co",
        company_url: null,
        location: null,
        employment_type: null,
        start_date: null,
        end_date: null,
        is_current: true,
        description_bullets: [],
        order_index: 0,
        role_taxonomy: null,
        record_meta: { ...META },
      },
    ],
    education: [
      {
        id: "ed1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        degree: "BSc",
        field_of_study: null,
        institution: "Uni",
        location: null,
        start_date: null,
        end_date: null,
        is_current: false,
        grade: null,
        description_bullets: [],
        relevant_coursework: [],
        order_index: 0,
        record_meta: { ...META },
      },
    ],
    projects: [
      {
        id: "p1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        title: "Studio",
        description: null,
        technologies: [],
        project_url: null,
        start_date: null,
        end_date: null,
        role: null,
        key_achievements: [],
        order_index: 0,
        skill_taxonomy: [],
        record_meta: { ...META },
      },
    ],
    skills: [
      {
        id: "s1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        name: "TypeScript",
        skill_type: "technical",
        category: null,
        proficiency: null,
        order_index: 0,
        taxonomy: null,
        record_meta: { ...META },
      },
    ],
    credentials: [
      {
        id: "c1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        credential_type: "certification",
        name: "CK Ref",
        issuing_organization: "CareerKundi",
        issue_date: null,
        expiry_date: null,
        credential_id: null,
        credential_url: null,
        order_index: 0,
        record_meta: { ...META },
      },
    ],
    targets: [
      {
        id: "t2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Staff Engineer",
        role_taxonomy: null,
        pathway_type: null,
        target_country: "UK",
        target_region: "London",
        target_industry: null,
        target_seniority: "senior",
        time_horizon: "12 months",
        priority: 2,
        order_index: 1,
        record_meta: { ...META },
      },
      {
        id: "t1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Platform Engineer",
        role_taxonomy: null,
        pathway_type: null,
        target_country: "UK",
        target_region: null,
        target_industry: null,
        target_seniority: "mid",
        time_horizon: "6 months",
        priority: 1,
        order_index: 0,
        record_meta: { ...META },
      },
    ],
  });
}

describe("passportIntegrationUtils", () => {
  it("reports empty readiness and no usable profile", () => {
    expect(passportHasUsableProfile(null)).toBe(false);
    expect(passportHasUsableProfile(emptyPassport())).toBe(false);
    expect(passportReadinessMessage(null)).toMatch(/not available/i);
    expect(passportReadinessMessage(emptyPassport())).toMatch(
      /does not have enough structured content/i,
    );
    expect(passportReadinessMessage(emptyPassport())).not.toMatch(
      /score|verified|strength/i,
    );
  });

  it("reports populated readiness and section counts", () => {
    const p = populatedPassport();
    expect(passportHasUsableProfile(p)).toBe(true);
    expect(passportReadinessMessage(p)).toMatch(/Career Passport available/i);
    expect(passportReadinessMessage(p)).toMatch(/Private and unverified/i);
    expect(passportSectionCounts(p)).toEqual({
      profile: 1,
      experience: 1,
      education: 1,
      projects: 1,
      skills: 1,
      credentials: 1,
      targets: 2,
    });
  });

  it("maps enabled CV section IDs and excludes empty/disabled/targets", () => {
    const p = populatedPassport();
    expect(passportEnabledCvSectionIds(p)).toEqual([
      "summary",
      "experience",
      "education",
      "skills",
      "projects",
      "certifications",
    ]);
    expect(passportEnabledCvSectionIds(p)).not.toContain("targets");

    const base = populatedPassport();
    const disabledSkills: PassportRead = {
      ...base,
      section_preferences: base.section_preferences.map((pref) =>
        pref.section === "skills" ? { ...pref, enabled: false } : pref,
      ),
    };
    expect(
      disabledSkills.section_preferences.find((p) => p.section === "skills")
        ?.enabled,
    ).toBe(false);
    expect(passportEnabledCvSectionIds(disabledSkills)).not.toContain("skills");

    const noCreds: PassportRead = { ...populatedPassport(), credentials: [] };
    expect(passportEnabledCvSectionIds(noCreds)).not.toContain("certifications");
  });

  it("builds target prefill list and primary text by priority", () => {
    const p = populatedPassport();
    expect(passportPrimaryTargetText(p)).toBe("Platform Engineer");
    const list = passportTargetsForPrefill(p);
    expect(list[0].target_role_text).toBe("Platform Engineer");
    expect(list[0].target_country).toBe("UK");
    expect(list[0].target_seniority).toBe("mid");
    expect(list[0].priority).toBe(1);
    expect(list[1].target_role_text).toBe("Staff Engineer");
  });

  it("builds Roadmap context without IDs or verification claims", () => {
    const target = passportTargetsForPrefill(populatedPassport())[0];
    const ctx = buildRoadmapContextFromPassportTarget(target);
    expect(ctx).toMatch(/Platform Engineer/);
    expect(ctx).toMatch(/Country: UK/);
    expect(ctx).toMatch(/Seniority: mid/);
    expect(ctx).toMatch(/Time horizon: 6 months/);
    expect(ctx).toMatch(/Priority: 1/);
    expect(ctx).not.toMatch(/t1|11111111|verified|score|wallet/i);
  });
});
