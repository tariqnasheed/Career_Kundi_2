/**
 * PassportEditForms tests (0052-F5).
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
  },
}));

import {
  PassportEducationEditor,
  PassportExperienceEditor,
  PassportProfileEditor,
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
    projects: [],
    skills: [],
    credentials: [],
    targets: [],
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
