/**
 * PassportPage tests (0052-F4/F5) — overview + Profile/Experience/Education editing.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { PassportRead } from "@/types/api";

const getMock = vi.fn();
const patchProfile = vi.fn();
const createExperience = vi.fn();
const createEducation = vi.fn();

vi.mock("@/lib/api", () => ({
  passportApi: {
    get: (...args: unknown[]) => getMock(...args),
    patchProfile: (...args: unknown[]) => patchProfile(...args),
    createExperience: (...args: unknown[]) => createExperience(...args),
    patchExperience: vi.fn(),
    deleteExperience: vi.fn(),
    reorderExperiences: vi.fn(),
    createEducation: (...args: unknown[]) => createEducation(...args),
    patchEducation: vi.fn(),
    deleteEducation: vi.fn(),
    reorderEducation: vi.fn(),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: (selector?: (s: { addToast: typeof vi.fn }) => unknown) => {
    const state = { addToast: vi.fn() };
    return selector ? selector(state) : state;
  },
}));

import PassportPage from "./PassportPage";

const UNVERIFIED_META = {
  source_status: "user_asserted",
  support_status: "profile_supported",
  verification_status: "unverified",
} as const;

const DEFAULT_PREFS = [
  { section: "profile" as const, order_index: 0, enabled: true },
  { section: "experience" as const, order_index: 1, enabled: true },
  { section: "education" as const, order_index: 2, enabled: true },
  { section: "projects" as const, order_index: 3, enabled: true },
  { section: "skills" as const, order_index: 4, enabled: true },
  { section: "credentials" as const, order_index: 5, enabled: true },
  { section: "targets" as const, order_index: 6, enabled: true },
];

function populatedFixture(overrides: Partial<PassportRead> = {}): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada Lovelace",
    headline: "Analytical Engineer",
    summary: "Building careful systems.",
    visibility: "private",
    version: 3,
    section_preferences: DEFAULT_PREFS,
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
      interests: [],
      record_meta: { ...UNVERIFIED_META },
    },
    experiences: [
      {
        id: "22222222-2222-2222-2222-222222222222",
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
        record_meta: { ...UNVERIFIED_META },
      },
    ],
    education: [
      {
        id: "33333333-3333-3333-3333-333333333333",
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
        record_meta: { ...UNVERIFIED_META },
      },
    ],
    projects: [
      {
        id: "44444444-4444-4444-4444-444444444444",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        title: "Difference Engine Notes",
        description: null,
        technologies: [],
        project_url: null,
        start_date: null,
        end_date: null,
        role: null,
        key_achievements: [],
        order_index: 0,
        skill_taxonomy: [],
        record_meta: { ...UNVERIFIED_META },
      },
    ],
    skills: [
      {
        id: "55555555-5555-5555-5555-555555555555",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        name: "Analysis",
        skill_type: "technical",
        category: null,
        proficiency: null,
        order_index: 0,
        taxonomy: null,
        record_meta: { ...UNVERIFIED_META },
      },
      {
        id: "66666666-6666-6666-6666-666666666666",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        name: "Writing",
        skill_type: "soft",
        category: null,
        proficiency: null,
        order_index: 1,
        taxonomy: null,
        record_meta: { ...UNVERIFIED_META },
      },
    ],
    credentials: [
      {
        id: "77777777-7777-7777-7777-777777777777",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        credential_type: "certification",
        name: "Computing Certificate",
        issuing_organization: "Society",
        issue_date: null,
        expiry_date: null,
        credential_id: null,
        credential_url: null,
        order_index: 0,
        record_meta: { ...UNVERIFIED_META },
      },
    ],
    targets: [
      {
        id: "88888888-8888-8888-8888-888888888888",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Staff Engineer",
        role_taxonomy: null,
        pathway_type: null,
        target_country: "UK",
        target_region: null,
        target_industry: null,
        target_seniority: "senior",
        time_horizon: "2 years",
        priority: 2,
        order_index: 0,
        record_meta: {
          source_status: "user_asserted",
          support_status: "not_provided",
          verification_status: "unverified",
        },
      },
    ],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-07-13T12:00:00Z",
    ...overrides,
  };
}

function emptyFixture(): PassportRead {
  return populatedFixture({
    display_name: "New User",
    headline: null,
    summary: null,
    version: 1,
    profile: {
      ...populatedFixture().profile,
      professional_headline: null,
      bio_summary: null,
    },
    experiences: [],
    education: [],
    projects: [],
    skills: [],
    credentials: [],
    targets: [],
  });
}

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PassportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PassportPage", () => {
  beforeEach(() => {
    getMock.mockReset();
    patchProfile.mockReset();
    createExperience.mockReset();
    createEducation.mockReset();
  });

  it("shows loading state with aria-busy and no fake user content", async () => {
    getMock.mockImplementation(() => new Promise(() => undefined));
    renderPage();
    expect(screen.getByLabelText(/loading your career passport/i)).toBeInTheDocument();
    expect(document.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(screen.queryByText("Ada Lovelace")).not.toBeInTheDocument();
  });

  it("renders populated passport without ownership fields", async () => {
    getMock.mockResolvedValue(populatedFixture());
    renderPage();
    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      /Career & Education Passport/i,
    );
    expect(screen.getAllByText("Private").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Unverified").length).toBeGreaterThan(0);
    expect(screen.getByText("Staff Engineer")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.queryByText(/owner_user_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/profile_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/"source_status"/)).not.toBeInTheDocument();
    expect(getMock).toHaveBeenCalledTimes(1);
  });

  it("renders neutral empty-state copy", async () => {
    getMock.mockResolvedValue(emptyFixture());
    renderPage();
    expect(
      await screen.findByText(/Your private Career Passport is ready/i),
    ).toBeInTheDocument();
  });

  it("shows Hidden in Passport view for disabled sections", async () => {
    const prefs = DEFAULT_PREFS.map((p) =>
      p.section === "projects" ? { ...p, enabled: false } : p,
    );
    getMock.mockResolvedValue(populatedFixture({ section_preferences: prefs }));
    renderPage();
    expect(await screen.findByText(/Hidden in Passport view/i)).toBeInTheDocument();
    expect(screen.getAllByText("Projects").length).toBeGreaterThan(0);
  });

  it("shows error state and retries via passportApi.get only", async () => {
    getMock
      .mockRejectedValueOnce({
        error: true,
        code: "INTERNAL_ERROR",
        message: "Passport temporarily unavailable.",
        details: {},
      })
      .mockResolvedValueOnce(populatedFixture());

    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /Passport temporarily unavailable/i,
    );
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    expect(getMock).toHaveBeenCalledTimes(2);
  });

  it("exposes edit controls only for Profile, Experience and Education", async () => {
    getMock.mockResolvedValue(populatedFixture());
    renderPage();
    expect(await screen.findByRole("button", { name: /edit profile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add experience/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add education/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add project/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add skill/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add credential/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add target/i })).not.toBeInTheDocument();
    expect(screen.getAllByText(/Editing arrives in a later Passport step/i).length).toBeGreaterThan(0);
  });

  it("updates headline from returned aggregate after profile edit", async () => {
    getMock.mockResolvedValue(populatedFixture());
    patchProfile.mockResolvedValue(
      populatedFixture({
        version: 4,
        headline: "Lead Analyst",
        profile: {
          ...populatedFixture().profile,
          professional_headline: "Lead Analyst",
        },
      }),
    );
    renderPage();
    expect(await screen.findByText("Analytical Engineer")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /edit profile/i }));
    fireEvent.change(screen.getByLabelText(/professional headline/i), {
      target: { value: "Lead Analyst" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save profile/i }));
    expect(await screen.findByText("Lead Analyst")).toBeInTheDocument();
    expect(screen.getByText(/Version 4/i)).toBeInTheDocument();
  });

  it("increases experience count after create from returned aggregate", async () => {
    getMock.mockResolvedValue(populatedFixture({ experiences: [] }));
    createExperience.mockResolvedValue(
      populatedFixture({
        version: 4,
        experiences: populatedFixture().experiences,
      }),
    );
    renderPage();
    expect(await screen.findByText("0")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /add experience/i }));
    fireEvent.change(screen.getByLabelText(/job title/i), {
      target: { value: "Engineer" },
    });
    fireEvent.change(screen.getByLabelText(/company name/i), {
      target: { value: "Analytical Engines" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save experience/i }));
    await waitFor(() =>
      expect(screen.getByText("Engineer")).toBeInTheDocument(),
    );
  });

  it("increases education count after create from returned aggregate", async () => {
    getMock.mockResolvedValue(populatedFixture({ education: [] }));
    createEducation.mockResolvedValue(
      populatedFixture({
        version: 4,
        education: populatedFixture().education,
      }),
    );
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /add education/i }));
    fireEvent.change(screen.getByLabelText(/^degree$/i), {
      target: { value: "Mathematics" },
    });
    fireEvent.change(screen.getByLabelText(/^institution$/i), {
      target: { value: "University" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save education/i }));
    expect(await screen.findByText("Mathematics")).toBeInTheDocument();
  });

  it("shows conflict warning and refetches", async () => {
    getMock
      .mockResolvedValueOnce(populatedFixture())
      .mockResolvedValueOnce(populatedFixture({ version: 5, headline: "Refetched" }));
    patchProfile.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "stale",
      details: {},
    });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /edit profile/i }));
    fireEvent.change(screen.getByLabelText(/professional headline/i), {
      target: { value: "Conflict attempt" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save profile/i }));
    expect(
      await screen.findByText(/Your Passport changed elsewhere/i),
    ).toBeInTheDocument();
    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(2));
  });
});
