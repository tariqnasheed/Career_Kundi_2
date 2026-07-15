/**
 * CVBuilderPage.test.tsx — 0052-F7 Passport awareness
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { PassportRead } from "@/types/api";

const passportGet = vi.fn();
const profileGet = vi.fn();
const jobList = vi.fn();
const cvList = vi.fn();
const cvGenerate = vi.fn();
const cvUpdate = vi.fn();

vi.mock("@/lib/api", () => ({
  passportApi: { get: (...args: unknown[]) => passportGet(...args) },
  profileApi: { get: (...args: unknown[]) => profileGet(...args) },
  jobApi: { list: (...args: unknown[]) => jobList(...args) },
  cvApi: {
    list: (...args: unknown[]) => cvList(...args),
    generate: (...args: unknown[]) => cvGenerate(...args),
    update: (...args: unknown[]) => cvUpdate(...args),
    downloadPdf: vi.fn(),
  },
  taxonomyApi: {
    matchRole: vi.fn(),
    getRole: vi.fn(),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: () => ({ addToast: vi.fn() }),
}));

vi.mock("@/components/features/CVTemplateGallery", () => ({
  CV_TEMPLATE_CATALOG: [{ id: "minimal-corporate", name: "Minimal" }],
  DEFAULT_TEMPLATE_ID: "minimal-corporate",
  getCVTemplate: () => ({
    id: "minimal-corporate",
    name: "Minimal",
    backendTemplate: "classic",
    atsLevel: "High",
  }),
  CVTemplateGallery: () => <div>Gallery</div>,
}));

vi.mock("@/components/features/CVTemplatePreview", () => ({
  CVTemplatePreview: () => <div>Preview</div>,
}));

vi.mock("@/components/features/CVBuilderStudioPanel", () => ({
  CVBuilderStudioPanel: (props: {
    enabledSections: string[];
    roleIntelligence: { targetRoleText: string };
    onRoleTextChange: (v: string) => void;
    onSectionsChange: (ids: string[]) => void;
  }) => (
    <div data-testid="studio-panel">
      <div data-testid="enabled-sections">{props.enabledSections.join(",")}</div>
      <div data-testid="role-text">{props.roleIntelligence.targetRoleText}</div>
      <button
        type="button"
        onClick={() => props.onRoleTextChange("manual")}
      >
        Manual role
      </button>
    </div>
  ),
}));

import CVBuilderPage from "./CVBuilderPage";

const META = {
  source_status: "user_asserted",
  support_status: "profile_supported" as const,
  verification_status: "unverified" as const,
};

function populatedPassport(): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada",
    headline: "Engineer",
    summary: "Summary",
    visibility: "private",
    version: 3,
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
      professional_headline: "Engineer",
      bio_summary: "Summary",
      declaration_text: null,
      references_available_on_request: false,
      interests: [],
      record_meta: { ...META },
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
    education: [],
    projects: [],
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
        name: "CK",
        issuing_organization: "CK",
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
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  };
}

function emptyPassport(): PassportRead {
  const p = populatedPassport();
  return {
    ...p,
    headline: null,
    summary: null,
    profile: { ...p.profile, professional_headline: null, bio_summary: null, interests: [] },
    experiences: [],
    education: [],
    projects: [],
    skills: [],
    credentials: [],
    targets: [],
  };
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <CVBuilderPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CVBuilderPage F7 Passport awareness", () => {
  beforeEach(() => {
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: {
        getItem: vi.fn(() => null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
    });
    passportGet.mockReset();
    profileGet.mockReset();
    jobList.mockReset();
    cvList.mockReset();
    cvGenerate.mockReset();
    cvUpdate.mockReset();
    profileGet.mockResolvedValue({
      full_name: "Ada",
      bio_summary: "x",
      professional_headline: "y",
      work_experiences: [{ title: "E" }],
    });
    jobList.mockResolvedValue([]);
    cvList.mockResolvedValue([]);
  });

  it("renders Passport card and empty copy when unused", async () => {
    passportGet.mockResolvedValue(emptyPassport());
    renderPage();
    expect(await screen.findByTestId("cv-passport-card")).toBeInTheDocument();
    expect(screen.getByText(/Private and unverified/i)).toBeInTheDocument();
    expect(
      await screen.findByText(/does not have enough structured content/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/verified passport|official credential|passport strength/i)).not.toBeInTheDocument();
  });

  it("applies Passport sections and target role without Passport mutations", async () => {
    passportGet.mockResolvedValue(populatedPassport());
    cvGenerate.mockResolvedValue({
      id: "cv1",
      name: "Ada CV",
      sections: {},
    });
    renderPage();
    expect(await screen.findByText(/Usable sections/i)).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /Use Passport sections for this CV/i }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("enabled-sections").textContent).toContain(
        "summary",
      ),
    );
    expect(screen.getByTestId("enabled-sections").textContent).toContain(
      "experience",
    );
    expect(screen.getByTestId("enabled-sections").textContent).toContain(
      "certifications",
    );
    fireEvent.click(screen.getByRole("button", { name: /^Platform Engineer$/i }));
    expect(screen.getByTestId("role-text")).toHaveTextContent("Platform Engineer");
    fireEvent.click(screen.getByRole("button", { name: /Save Draft/i }));
    await waitFor(() => expect(cvGenerate).toHaveBeenCalled());
    const payload = cvGenerate.mock.calls[0][0];
    expect(payload.passport_id).toBeUndefined();
    expect(JSON.stringify(payload)).not.toMatch(/passport_id/);
    expect(payload.section_ids).toEqual(
      expect.arrayContaining(["summary", "experience", "skills", "certifications"]),
    );
  });

  it("does not block CV workspace when Passport fails", async () => {
    passportGet.mockRejectedValue({
      error: true,
      code: "INTERNAL_ERROR",
      message: "down",
      details: {},
    });
    renderPage();
    expect(await screen.findByTestId("studio-panel")).toBeInTheDocument();
    expect(
      await screen.findByText(/Career Passport could not be loaded/i),
    ).toBeInTheDocument();
  });
});
