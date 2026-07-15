/**
 * PassportEditForms tests (0052-F5/F6).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { PassportRead } from "@/types/api";

const patchProfile = vi.fn();
const createExperience = vi.fn();
const patchExperience = vi.fn();
const deleteExperience = vi.fn();
const reorderExperiences = vi.fn();
const createEducation = vi.fn();
const patchEducation = vi.fn();
const deleteEducation = vi.fn();
const reorderEducation = vi.fn();
const createProject = vi.fn();
const patchProject = vi.fn();
const deleteProject = vi.fn();
const reorderProjects = vi.fn();
const createSkill = vi.fn();
const patchSkill = vi.fn();
const deleteSkill = vi.fn();
const reorderSkills = vi.fn();
const createCredential = vi.fn();
const patchCredential = vi.fn();
const deleteCredential = vi.fn();
const reorderCredentials = vi.fn();
const createTarget = vi.fn();
const patchTarget = vi.fn();
const deleteTarget = vi.fn();
const reorderTargets = vi.fn();

vi.mock("@/lib/api", () => ({
  passportApi: {
    patchProfile: (...args: unknown[]) => patchProfile(...args),
    createExperience: (...args: unknown[]) => createExperience(...args),
    patchExperience: (...args: unknown[]) => patchExperience(...args),
    deleteExperience: (...args: unknown[]) => deleteExperience(...args),
    reorderExperiences: (...args: unknown[]) => reorderExperiences(...args),
    createEducation: (...args: unknown[]) => createEducation(...args),
    patchEducation: (...args: unknown[]) => patchEducation(...args),
    deleteEducation: (...args: unknown[]) => deleteEducation(...args),
    reorderEducation: (...args: unknown[]) => reorderEducation(...args),
    createProject: (...args: unknown[]) => createProject(...args),
    patchProject: (...args: unknown[]) => patchProject(...args),
    deleteProject: (...args: unknown[]) => deleteProject(...args),
    reorderProjects: (...args: unknown[]) => reorderProjects(...args),
    createSkill: (...args: unknown[]) => createSkill(...args),
    patchSkill: (...args: unknown[]) => patchSkill(...args),
    deleteSkill: (...args: unknown[]) => deleteSkill(...args),
    reorderSkills: (...args: unknown[]) => reorderSkills(...args),
    createCredential: (...args: unknown[]) => createCredential(...args),
    patchCredential: (...args: unknown[]) => patchCredential(...args),
    deleteCredential: (...args: unknown[]) => deleteCredential(...args),
    reorderCredentials: (...args: unknown[]) => reorderCredentials(...args),
    createTarget: (...args: unknown[]) => createTarget(...args),
    patchTarget: (...args: unknown[]) => patchTarget(...args),
    deleteTarget: (...args: unknown[]) => deleteTarget(...args),
    reorderTargets: (...args: unknown[]) => reorderTargets(...args),
  },
}));

import {
  PassportCredentialEditor,
  PassportEducationEditor,
  PassportExperienceEditor,
  PassportProfileEditor,
  PassportProjectEditor,
  PassportSkillEditor,
  PassportTargetEditor,
} from "./PassportEditForms";

const META = {
  source_status: "user_asserted",
  support_status: "profile_supported",
  verification_status: "unverified",
} as const;

function basePassport(overrides: Partial<PassportRead> = {}): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada Lovelace",
    headline: "Analytical Engineer",
    summary: "Building careful systems.",
    visibility: "private",
    version: 3,
    section_preferences: [],
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
      professional_headline: "Analytical Engineer",
      bio_summary: "Building careful systems.",
      declaration_text: null,
      references_available_on_request: false,
      interests: ["Math"],
      record_meta: { ...META },
    },
    experiences: [
      {
        id: "e1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        job_title: "Engineer",
        company_name: "Analytical Engines",
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
      {
        id: "e2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        job_title: "Analyst",
        company_name: "Notes Co",
        company_url: null,
        location: null,
        employment_type: null,
        start_date: null,
        end_date: null,
        is_current: false,
        description_bullets: [],
        order_index: 1,
        role_taxonomy: null,
        record_meta: { ...META },
      },
    ],
    education: [
      {
        id: "ed1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        degree: "Mathematics",
        field_of_study: null,
        institution: "University",
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
        title: "Alpha Project",
        description: null,
        technologies: ["React"],
        project_url: null,
        start_date: null,
        end_date: null,
        role: null,
        key_achievements: [],
        order_index: 0,
        skill_taxonomy: [],
        record_meta: { ...META },
      },
      {
        id: "p2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        title: "Beta Project",
        description: null,
        technologies: [],
        project_url: null,
        start_date: null,
        end_date: null,
        role: null,
        key_achievements: [],
        order_index: 1,
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
        proficiency: "advanced",
        order_index: 0,
        taxonomy: null,
        record_meta: { ...META },
      },
      {
        id: "s2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        name: "Communication",
        skill_type: "soft",
        category: null,
        proficiency: null,
        order_index: 1,
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
        name: "AWS Practitioner",
        issuing_organization: "Amazon",
        issue_date: null,
        expiry_date: null,
        credential_id: null,
        credential_url: null,
        order_index: 0,
        record_meta: { ...META },
      },
      {
        id: "c2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        credential_type: "license",
        name: "Driving Permit",
        issuing_organization: "DVLA",
        issue_date: null,
        expiry_date: null,
        credential_id: null,
        credential_url: null,
        order_index: 1,
        record_meta: { ...META },
      },
    ],
    targets: [
      {
        id: "t1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Staff Engineer",
        role_taxonomy: null,
        pathway_type: null,
        target_country: "UK",
        target_region: null,
        target_industry: null,
        target_seniority: "senior",
        time_horizon: "12 months",
        priority: 2,
        order_index: 0,
        record_meta: { ...META },
      },
      {
        id: "t2",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Engineering Manager",
        role_taxonomy: null,
        pathway_type: null,
        target_country: null,
        target_region: null,
        target_industry: null,
        target_seniority: null,
        time_horizon: null,
        priority: 3,
        order_index: 1,
        record_meta: { ...META },
      },
    ],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-07-13T12:00:00Z",
    ...overrides,
  };
}

describe("PassportProfileEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("sends changed fields plus expected_version and can clear a field", async () => {
    const onSaved = vi.fn();
    const onConflict = vi.fn();
    const next = basePassport({
      version: 4,
      headline: "Updated headline",
      profile: {
        ...basePassport().profile,
        professional_headline: "Updated headline",
        bio_summary: null,
      },
    });
    patchProfile.mockResolvedValue(next);

    render(
      <PassportProfileEditor
        passport={basePassport()}
        onSaved={onSaved}
        onConflict={onConflict}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /edit profile/i }));
    fireEvent.change(screen.getByLabelText(/professional headline/i), {
      target: { value: "Updated headline" },
    });
    fireEvent.change(screen.getByLabelText(/^summary$/i), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save profile/i }));

    await waitFor(() => expect(patchProfile).toHaveBeenCalledTimes(1));
    expect(patchProfile).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        professional_headline: "Updated headline",
        bio_summary: null,
      }),
    );
    expect(onSaved).toHaveBeenCalledWith(next);
    expect(onConflict).not.toHaveBeenCalled();
  });

  it("calls onConflict on CONFLICT", async () => {
    const onSaved = vi.fn();
    const onConflict = vi.fn();
    patchProfile.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "Version conflict",
      details: {},
    });

    render(
      <PassportProfileEditor
        passport={basePassport()}
        onSaved={onSaved}
        onConflict={onConflict}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /edit profile/i }));
    fireEvent.change(screen.getByLabelText(/professional headline/i), {
      target: { value: "X" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save profile/i }));
    await waitFor(() => expect(onConflict).toHaveBeenCalled());
    expect(onSaved).not.toHaveBeenCalled();
  });
});

describe("PassportExperienceEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("blocks missing title/company and creates with expected_version", async () => {
    const onSaved = vi.fn();
    createExperience.mockResolvedValue(basePassport({ version: 4 }));

    render(
      <PassportExperienceEditor
        passport={basePassport()}
        onSaved={onSaved}
        onConflict={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));
    fireEvent.click(screen.getByRole("button", { name: /save experience/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/job title/i);
    expect(createExperience).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/job title/i), {
      target: { value: "Staff Engineer" },
    });
    fireEvent.change(screen.getByLabelText(/company name/i), {
      target: { value: "CK Labs" },
    });
    fireEvent.click(screen.getByLabelText(/current role/i));
    fireEvent.change(screen.getByLabelText(/end date/i), {
      target: { value: "2020-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save experience/i }));

    await waitFor(() => expect(createExperience).toHaveBeenCalled());
    expect(createExperience).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        job_title: "Staff Engineer",
        company_name: "CK Labs",
        is_current: true,
        end_date: null,
      }),
    );
  });

  it("blocks invalid date order", async () => {
    render(
      <PassportExperienceEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));
    fireEvent.change(screen.getByLabelText(/job title/i), {
      target: { value: "Engineer" },
    });
    fireEvent.change(screen.getByLabelText(/company name/i), {
      target: { value: "Co" },
    });
    fireEvent.change(screen.getByLabelText(/start date/i), {
      target: { value: "2022-01-01" },
    });
    fireEvent.change(screen.getByLabelText(/end date/i), {
      target: { value: "2020-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save experience/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/end date/i);
    expect(createExperience).not.toHaveBeenCalled();
  });

  it("delete confirms and sends expected_version", async () => {
    deleteExperience.mockResolvedValue(basePassport({ version: 4, experiences: [] }));
    render(
      <PassportExperienceEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^delete$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() =>
      expect(deleteExperience).toHaveBeenCalledWith("e1", 3),
    );
  });

  it("reorder sends full ordered ids", async () => {
    reorderExperiences.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportExperienceEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /move engineer down/i }));
    await waitFor(() => expect(reorderExperiences).toHaveBeenCalled());
    expect(reorderExperiences).toHaveBeenCalledWith({
      expected_version: 3,
      ordered_ids: ["e2", "e1"],
    });
  });
});

describe("PassportEducationEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("creates education with normalized coursework and expected_version", async () => {
    createEducation.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportEducationEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add education/i }));
    fireEvent.change(screen.getByLabelText(/^degree$/i), {
      target: { value: "MSc" },
    });
    fireEvent.change(screen.getByLabelText(/^institution$/i), {
      target: { value: "College" },
    });
    fireEvent.change(screen.getByLabelText(/relevant coursework/i), {
      target: { value: "Algebra\n\nCalculus\nalgebra" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save education/i }));
    await waitFor(() => expect(createEducation).toHaveBeenCalled());
    expect(createEducation).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        degree: "MSc",
        institution: "College",
        relevant_coursework: ["Algebra", "Calculus"],
      }),
    );
  });

  it("blocks missing degree/institution", async () => {
    render(
      <PassportEducationEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add education/i }));
    fireEvent.click(screen.getByRole("button", { name: /save education/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/degree/i);
    expect(createEducation).not.toHaveBeenCalled();
  });

  it("handles conflict on delete", async () => {
    const onConflict = vi.fn();
    deleteEducation.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "stale",
      details: {},
    });
    render(
      <PassportEducationEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={onConflict}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => expect(onConflict).toHaveBeenCalled());
  });
});


describe("PassportProjectEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("adds project with title + expected_version and normalizes technologies", async () => {
    const onSaved = vi.fn();
    createProject.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportProjectEditor
        passport={basePassport({ projects: [] })}
        onSaved={onSaved}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add project/i }));
    fireEvent.click(screen.getByRole("button", { name: /save project/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/title/i);
    expect(createProject).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText(/^title$/i), {
      target: { value: "Passport Studio" },
    });
    fireEvent.change(screen.getByLabelText(/^technologies$/i), {
      target: { value: "React, , TypeScript, react" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save project/i }));
    await waitFor(() => expect(createProject).toHaveBeenCalled());
    expect(createProject).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        title: "Passport Studio",
        technologies: ["React", "TypeScript"],
      }),
    );
    expect(onSaved).toHaveBeenCalled();
  });

  it("blocks invalid date order", async () => {
    render(
      <PassportProjectEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add project/i }));
    fireEvent.change(screen.getByLabelText(/^title$/i), {
      target: { value: "X" },
    });
    fireEvent.change(screen.getByLabelText(/start date/i), {
      target: { value: "2022-01-01" },
    });
    fireEvent.change(screen.getByLabelText(/end date/i), {
      target: { value: "2020-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save project/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/end date/i);
    expect(createProject).not.toHaveBeenCalled();
  });

  it("delete confirms and reorder sends full ordered ids; conflict calls onConflict", async () => {
    const onConflict = vi.fn();
    deleteProject.mockResolvedValue(basePassport({ version: 4, projects: [] }));
    reorderProjects.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "stale",
      details: {},
    });
    render(
      <PassportProjectEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={onConflict}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^delete$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => expect(deleteProject).toHaveBeenCalledWith("p1", 3));

    fireEvent.click(screen.getByRole("button", { name: /move alpha project down/i }));
    await waitFor(() => expect(onConflict).toHaveBeenCalled());
    expect(reorderProjects).toHaveBeenCalledWith({
      expected_version: 3,
      ordered_ids: ["p2", "p1"],
    });
  });
});

describe("PassportSkillEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("adds skill with name/type + expected_version and blocks missing name", async () => {
    createSkill.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportSkillEditor
        passport={basePassport({ skills: [] })}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /add skill/i }));
    fireEvent.click(screen.getByRole("button", { name: /save skill/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/skill name/i);
    expect(createSkill).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText(/^name$/i), {
      target: { value: "Python" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save skill/i }));
    await waitFor(() => expect(createSkill).toHaveBeenCalled());
    expect(createSkill).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        name: "Python",
        skill_type: "technical",
      }),
    );
  });

  it("edit skill sends changed fields and reorder/delete work", async () => {
    patchSkill.mockResolvedValue(basePassport({ version: 4 }));
    deleteSkill.mockResolvedValue(basePassport({ version: 5, skills: [] }));
    reorderSkills.mockResolvedValue(basePassport({ version: 6 }));
    render(
      <PassportSkillEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^edit$/i })[0]);
    fireEvent.change(screen.getByLabelText(/^name$/i), {
      target: { value: "TypeScript Advanced" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save skill/i }));
    await waitFor(() =>
      expect(patchSkill).toHaveBeenCalledWith(
        "s1",
        expect.objectContaining({
          expected_version: 3,
          name: "TypeScript Advanced",
        }),
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: /move typescript down/i }));
    await waitFor(() =>
      expect(reorderSkills).toHaveBeenCalledWith({
        expected_version: 3,
        ordered_ids: ["s2", "s1"],
      }),
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^delete$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => expect(deleteSkill).toHaveBeenCalledWith("s1", 3));
  });
});

describe("PassportCredentialEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("adds credential and blocks missing name/org and bad expiry", async () => {
    createCredential.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportCredentialEditor
        passport={basePassport({ credentials: [] })}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    expect(
      screen.getAllByText(/Credential reference/i).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/verified credential/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /add credential/i }));
    fireEvent.click(screen.getByRole("button", { name: /save credential/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/credential name/i);
    fireEvent.change(screen.getByLabelText(/^name$/i), {
      target: { value: "CK Cert" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save credential/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/issuing organization/i);
    fireEvent.change(screen.getByLabelText(/issuing organization/i), {
      target: { value: "CareerKundi" },
    });
    fireEvent.change(screen.getByLabelText(/issue date/i), {
      target: { value: "2024-01-01" },
    });
    fireEvent.change(screen.getByLabelText(/expiry date/i), {
      target: { value: "2023-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save credential/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/expiry date/i);
    expect(createCredential).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText(/expiry date/i), {
      target: { value: "2025-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save credential/i }));
    await waitFor(() => expect(createCredential).toHaveBeenCalled());
    expect(createCredential).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        name: "CK Cert",
        issuing_organization: "CareerKundi",
        credential_type: "certification",
      }),
    );
  });

  it("delete confirmation and reorder", async () => {
    deleteCredential.mockResolvedValue(basePassport({ version: 4, credentials: [] }));
    reorderCredentials.mockResolvedValue(basePassport({ version: 5 }));
    render(
      <PassportCredentialEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={vi.fn()}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^delete$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => expect(deleteCredential).toHaveBeenCalledWith("c1", 3));
    fireEvent.click(
      screen.getByRole("button", { name: /move aws practitioner down/i }),
    );
    await waitFor(() =>
      expect(reorderCredentials).toHaveBeenCalledWith({
        expected_version: 3,
        ordered_ids: ["c2", "c1"],
      }),
    );
  });
});

describe("PassportTargetEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("adds target with role + expected_version and clamps priority", async () => {
    const onConflict = vi.fn();
    createTarget.mockResolvedValue(basePassport({ version: 4 }));
    render(
      <PassportTargetEditor
        passport={basePassport({ targets: [] })}
        onSaved={vi.fn()}
        onConflict={onConflict}
      />,
    );
    expect(screen.getAllByText(/Not a Roadmap yet/i).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /add target/i }));
    fireEvent.click(screen.getByRole("button", { name: /save target/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/target role/i);
    expect(createTarget).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText(/target role/i), {
      target: { value: "Platform Engineer" },
    });
    fireEvent.change(screen.getByLabelText(/^priority$/i), {
      target: { value: "9" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save target/i }));
    await waitFor(() => expect(createTarget).toHaveBeenCalled());
    expect(createTarget).toHaveBeenCalledWith(
      expect.objectContaining({
        expected_version: 3,
        target_role_text: "Platform Engineer",
        priority: 5,
      }),
    );
  });

  it("delete confirmation, reorder, and conflict", async () => {
    const onConflict = vi.fn();
    deleteTarget.mockResolvedValue(basePassport({ version: 4, targets: [] }));
    reorderTargets.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "stale",
      details: {},
    });
    render(
      <PassportTargetEditor
        passport={basePassport()}
        onSaved={vi.fn()}
        onConflict={onConflict}
      />,
    );
    fireEvent.click(screen.getAllByRole("button", { name: /^delete$/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));
    await waitFor(() => expect(deleteTarget).toHaveBeenCalledWith("t1", 3));
    fireEvent.click(screen.getByRole("button", { name: /move staff engineer down/i }));
    await waitFor(() => expect(onConflict).toHaveBeenCalled());
    expect(reorderTargets).toHaveBeenCalledWith({
      expected_version: 3,
      ordered_ids: ["t2", "t1"],
    });
  });
});
