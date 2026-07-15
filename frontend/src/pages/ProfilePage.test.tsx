/**
 * ProfilePage.test.tsx — 0052-F7 Profile compatibility
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { PassportRead } from "@/types/api";

const profileGet = vi.fn();
const profileUpdate = vi.fn();
const passportGet = vi.fn();

vi.mock("@/lib/api", () => ({
  profileApi: {
    get: (...args: unknown[]) => profileGet(...args),
    update: (...args: unknown[]) => profileUpdate(...args),
  },
  passportApi: {
    get: (...args: unknown[]) => passportGet(...args),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: () => ({ addToast: vi.fn() }),
}));

import ProfilePage from "./ProfilePage";

const META = {
  source_status: "user_asserted",
  support_status: "profile_supported" as const,
  verification_status: "unverified" as const,
};

function passportFixture(): PassportRead {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    subject_id: null,
    display_name: "Ada",
    headline: "Engineer",
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
      professional_headline: "Engineer",
      bio_summary: "Summary",
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
  };
}

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProfilePage F7 compatibility", () => {
  beforeEach(() => {
    profileGet.mockReset();
    profileUpdate.mockReset();
    passportGet.mockReset();
    profileGet.mockResolvedValue({
      full_name: "Ada Lovelace",
      email: "ada@example.com",
      phone: "",
      location: "",
      linkedin_url: "",
      github_url: "",
      summary: "Analytical Engineer",
      experience: [],
      education: [],
      skills: [],
      certifications: [],
      projects: [],
    });
  });

  it("renders Passport compatibility card and removes old source-of-truth wording", async () => {
    passportGet.mockResolvedValue(passportFixture());
    renderPage();
    expect(await screen.findByDisplayValue("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByTestId("passport-compatibility-card")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Career Passport is now the primary structured editor/i).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/single source of truth/i)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Your data feeds every AI feature/i),
    ).not.toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Open Career Passport/i });
    expect(link).toHaveAttribute("href", "/passport");
    expect(screen.queryByText(/owner_user_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/profile_id/i)).not.toBeInTheDocument();
    expect(passportGet).toHaveBeenCalled();
    expect(profileUpdate).not.toHaveBeenCalled();
  });

  it("keeps Profile usable when Passport query fails", async () => {
    passportGet.mockRejectedValue({
      error: true,
      code: "INTERNAL_ERROR",
      message: "down",
      details: {},
    });
    renderPage();
    expect(await screen.findByDisplayValue("Ada Lovelace")).toBeInTheDocument();
    expect(
      await screen.findByText(/Career Passport could not be loaded/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open Career Passport/i })).toBeInTheDocument();
    await waitFor(() => expect(passportGet).toHaveBeenCalled());
  });

  it("renders Passport-synced object skills without crashing", async () => {
    passportGet.mockResolvedValue(passportFixture());
    profileGet.mockResolvedValue({
      full_name: "Ada Lovelace",
      email: "ada@example.com",
      phone: "",
      location: "",
      linkedin_url: "",
      github_url: "",
      summary: "Analytical Engineer",
      experience: [],
      education: [],
      skills: [
        {
          id: "s1",
          name: "TypeScript",
          skill_type: "technical",
          category: null,
          proficiency: null,
          order_index: 0,
        },
      ],
      certifications: [{ name: "AWS SAA", issuing_organization: "Amazon" }],
      projects: [],
    });
    renderPage();
    expect(await screen.findByDisplayValue("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByTestId("passport-compatibility-card")).toBeInTheDocument();
    expect(screen.getByText("TypeScript")).toBeInTheDocument();
    expect(screen.getByDisplayValue("AWS SAA")).toBeInTheDocument();
  });
});
