/**
 * EvidenceLibraryPage.test.tsx — 0053-F4 private metadata UI boundary.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

const listEvidence = vi.fn();
const createEvidenceMetadata = vi.fn();
const getEvidenceMetadata = vi.fn();
const listPlatformSubjects = vi.fn();
const addToast = vi.fn();

vi.mock("@/lib/api", () => ({
  evidenceApi: {
    listEvidence: (...args: unknown[]) => listEvidence(...args),
    createEvidenceMetadata: (...args: unknown[]) => createEvidenceMetadata(...args),
    getEvidenceMetadata: (...args: unknown[]) => getEvidenceMetadata(...args),
  },
  platformApi: {
    listPlatformSubjects: (...args: unknown[]) => listPlatformSubjects(...args),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: () => ({ addToast }),
}));

import EvidenceLibraryPage from "./EvidenceLibraryPage";

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EvidenceLibraryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const sampleRecord = {
  id: "11111111-1111-1111-1111-111111111111",
  subject_id: null,
  title: "Degree scan metadata",
  evidence_kind: "transcript",
  privacy_class: "private",
  storage_uri: null,
  content_hash: null,
  mime_type: null,
  size_bytes: null,
  source_id: null,
  snapshot_id: null,
  evidence_kind_label: "Transcript material",
  privacy_label: "Private",
  truth_warning:
    "Evidence material linked to a claim is private metadata only. A link is not independent review and does not change verification status.",
  created_at: "2026-07-16T10:00:00Z",
  updated_at: "2026-07-16T10:00:00Z",
};

describe("EvidenceLibraryPage F4 boundary", () => {
  beforeEach(() => {
    listEvidence.mockReset();
    createEvidenceMetadata.mockReset();
    getEvidenceMetadata.mockReset();
    listPlatformSubjects.mockReset();
    addToast.mockReset();
    listPlatformSubjects.mockResolvedValue([]);
    listEvidence.mockResolvedValue([]);
  });

  it("renders Evidence Library title and safe private metadata copy", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: /Evidence Library/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Private evidence library/i)).toBeInTheDocument();
    expect(screen.getByText(/Metadata only in this version/i)).toBeInTheDocument();
    expect(screen.getByText(/No file upload yet/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/not independently verified/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Linking evidence does not independently confirm a claim/i),
    ).toBeInTheDocument();
  });

  it("has no file upload, verify, or share controls", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /Evidence Library/i });
    expect(document.querySelector('input[type="file"]')).toBeNull();
    expect(
      screen.queryByRole("button", { name: /upload evidence/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /verify/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /share|publish/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Save evidence metadata/i }),
    ).toBeInTheDocument();
  });

  it("shows empty state when API returns no records", async () => {
    renderPage();
    expect(
      await screen.findByText(/No evidence metadata saved yet/i),
    ).toBeInTheDocument();
  });

  it("renders returned evidence records", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    expect(await screen.findByText("Degree scan metadata")).toBeInTheDocument();
    expect(screen.getByText(/Transcript material/i)).toBeInTheDocument();
    expect(screen.getAllByText(/private metadata only/i).length).toBeGreaterThan(0);
  });

  it("submits metadata payload without owner_user_id", async () => {
    createEvidenceMetadata.mockResolvedValue(sampleRecord);
    listEvidence.mockResolvedValue([]);
    renderPage();
    await screen.findByRole("heading", { name: /Evidence Library/i });

    fireEvent.change(screen.getByLabelText(/^Title$/i), {
      target: { value: "  Degree scan metadata  " },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Save evidence metadata/i }),
    );

    await waitFor(() => expect(createEvidenceMetadata).toHaveBeenCalledTimes(1));
    const payload = createEvidenceMetadata.mock.calls[0][0];
    expect(payload.title).toBe("Degree scan metadata");
    expect(payload.evidence_kind).toBe("document");
    expect(payload.privacy_class).toBe("private");
    expect(payload).not.toHaveProperty("owner_user_id");
    expect(JSON.stringify(payload)).not.toMatch(/owner_user_id/);
  });

  it("forbids unsafe trust wording except Not independently verified", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /Evidence Library/i });
    const text = document.body.textContent?.toLowerCase() ?? "";
    for (const forbidden of [
      "official",
      "trusted",
      "proof of truth",
      "public credential",
      "wallet",
      "blockchain",
      "did",
    ]) {
      expect(text).not.toContain(forbidden);
    }
    expect(text).toContain("not independently verified");
    const withoutSafe = text
      .split("not independently verified")
      .join("")
      .split("is not independently verified")
      .join("");
    expect(withoutSafe).not.toContain("verified");
  });

  it("mentions claim linking deferred without a claim UUID form", async () => {
    renderPage();
    expect(
      await screen.findByText(
        /Claim linking will be added after claim selection UI is available/i,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/claim id/i)).not.toBeInTheDocument();
  });
});
