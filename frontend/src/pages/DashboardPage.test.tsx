/**
 * DashboardPage.test.tsx — 0052-F8 Dashboard Roadmap-fetch watch.
 * Documents incidental roadmapApi.list as unrelated to Passport surfaces.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

const jobList = vi.fn();
const roadmapList = vi.fn();
const badgeStats = vi.fn();
const pendingCelebrations = vi.fn();

vi.mock("@/lib/api", () => ({
  jobApi: { list: (...args: unknown[]) => jobList(...args) },
  roadmapApi: { list: (...args: unknown[]) => roadmapList(...args) },
  badgeApi: {
    getStats: (...args: unknown[]) => badgeStats(...args),
    getPendingCelebrations: (...args: unknown[]) => pendingCelebrations(...args),
  },
}));

vi.mock("@/store/auth", () => ({
  useAuthStore: () => ({
    user: { full_name: "Ada Lovelace", email: "ada@example.com" },
  }),
}));

import DashboardPage from "./DashboardPage";

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardPage F8 Roadmap fetch watch", () => {
  beforeEach(() => {
    jobList.mockReset();
    roadmapList.mockReset();
    badgeStats.mockReset();
    pendingCelebrations.mockReset();
    jobList.mockResolvedValue([]);
    badgeStats.mockResolvedValue({ total_earned: 0 });
    pendingCelebrations.mockResolvedValue([]);
  });

  it("still shows core Dashboard content when Roadmap list fails", async () => {
    roadmapList.mockRejectedValue(new Error("roadmap unavailable"));
    renderPage();
    expect(await screen.findByText(/Good morning, Ada/i)).toBeInTheDocument();
    expect(screen.getByText(/career progress at a glance/i)).toBeInTheDocument();
    await waitFor(() => expect(roadmapList).toHaveBeenCalled());
    // Soft-fail: no catastrophic blank; empty roadmap card copy remains usable
    expect(await screen.findByText(/No roadmap yet/i)).toBeInTheDocument();
  });

  it("documents incidental Roadmap fetch is unrelated to Passport APIs", async () => {
    roadmapList.mockResolvedValue([]);
    renderPage();
    await waitFor(() => expect(roadmapList).toHaveBeenCalled());
    expect(screen.queryByText(/Career Passport/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Verified Passport|Passport strength|Profile score/i)).not.toBeInTheDocument();
  });
});
