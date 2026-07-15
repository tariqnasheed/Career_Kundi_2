/**
 * RoadmapPage.test.tsx — 0052-F7 Passport target prefill
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { PassportRead } from "@/types/api";

const passportGet = vi.fn();
const roadmapList = vi.fn();
const roadmapGenerate = vi.fn();
const roadmapGet = vi.fn();

vi.mock("@/lib/api", () => ({
  passportApi: { get: (...args: unknown[]) => passportGet(...args) },
  roadmapApi: {
    list: (...args: unknown[]) => roadmapList(...args),
    get: (...args: unknown[]) => roadmapGet(...args),
    generate: (...args: unknown[]) => roadmapGenerate(...args),
    updateSkillStatus: vi.fn(),
    refreshSkill: vi.fn(),
    delete: vi.fn(),
    regenerate: vi.fn(),
  },
  taxonomyApi: {
    matchRole: vi.fn(),
    getRole: vi.fn(),
    getRoleSkills: vi.fn(),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: () => ({ addToast: vi.fn() }),
}));

vi.mock("@/components/features/SkillRadar", () => ({
  SkillRadar: () => <div>Radar</div>,
}));

import RoadmapPage from "./RoadmapPage";

const META = {
  source_status: "user_asserted",
  support_status: "profile_supported" as const,
  verification_status: "unverified" as const,
};

function passportWithTarget(): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada",
    headline: null,
    summary: null,
    visibility: "private",
    version: 2,
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
    targets: [
      {
        id: "t1",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        target_role_text: "Platform Engineer",
        role_taxonomy: null,
        pathway_type: null,
        target_country: "UK",
        target_region: "London",
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

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <RoadmapPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("RoadmapPage F7 Passport target prefill", () => {
  beforeEach(() => {
    passportGet.mockReset();
    roadmapList.mockReset();
    roadmapGenerate.mockReset();
    roadmapGet.mockReset();
    roadmapList.mockResolvedValue([]);
    passportGet.mockResolvedValue(passportWithTarget());
  });

  it("shows Passport target prefill and generates Roadmap-owned payload", async () => {
    roadmapGenerate.mockResolvedValue({
      id: "r1",
      target_role: "Platform Engineer",
      milestones: [],
      skills: [],
    });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /New roadmap/i }));
    expect(
      await screen.findByText(/Use a Career Passport target/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/This creates a new Roadmap\. It does not change your Passport target/i),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^Platform Engineer$/i }));
    expect(screen.getByLabelText(/Target role/i)).toHaveValue("Platform Engineer");
    fireEvent.click(screen.getByRole("button", { name: /Generate roadmap/i }));
    await waitFor(() => expect(roadmapGenerate).toHaveBeenCalled());
    const payload = roadmapGenerate.mock.calls[0][0];
    expect(payload.target_role).toBe("Platform Engineer");
    expect(payload.personalization_inputs.passport_target_prefill).toEqual(
      expect.objectContaining({
        target_role_text: "Platform Engineer",
        target_country: "UK",
        target_seniority: "mid",
        priority: 1,
      }),
    );
    expect(payload.personalization_inputs.passport_target_prefill).not.toHaveProperty(
      "id",
    );
    expect(payload).not.toHaveProperty("passport_id");
    expect(passportGet).toHaveBeenCalled();
  });

  it("keeps generation usable when Passport fails", async () => {
    passportGet.mockRejectedValue({
      error: true,
      code: "INTERNAL_ERROR",
      message: "down",
      details: {},
    });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: /New roadmap/i }));
    expect(
      await screen.findByText(/Passport targets could not be loaded/i),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Target role/i), {
      target: { value: "Data Engineer" },
    });
    expect(screen.getByRole("button", { name: /Generate roadmap/i })).not.toBeDisabled();
  });
});
