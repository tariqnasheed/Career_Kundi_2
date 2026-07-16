/**
 * PassportEvidencePanel tests (0053-F8) — read-only private evidence awareness.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type { PassportEvidenceSummaryRead } from "@/types/api";

const getEvidencePassportSummary = vi.fn();

vi.mock("@/lib/api", () => ({
  evidenceApi: {
    getEvidencePassportSummary: (...args: unknown[]) =>
      getEvidencePassportSummary(...args),
  },
}));

import PassportEvidencePanel from "./PassportEvidencePanel";

const emptySummary: PassportEvidenceSummaryRead = {
  linked_claims_count: 0,
  evidence_records_count: 0,
  items: [],
  truth_warning:
    "Evidence linked here is private and not independently verified. Linking evidence does not verify your Passport, your profile, or a claim.",
};

const linkedSummary: PassportEvidenceSummaryRead = {
  linked_claims_count: 1,
  evidence_records_count: 1,
  items: [
    {
      claim_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      subject_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      claim_kind: "skill",
      claim_value: "Python",
      claim_support_status: "not_provided",
      claim_support_label: "Not supported yet",
      claim_verification_status: "unverified",
      claim_verification_label: "Not independently verified",
      link_role: "supports",
      link_role_label: "Linked as support material",
      evidence_id: "cccccccc-cccc-cccc-cccc-cccccccccccc",
      evidence_title: "Cert metadata",
      evidence_kind: "certificate",
      evidence_kind_label: "Certificate material",
      has_attachment: true,
      truth_warning:
        "A source or snapshot link is not verification. This claim is private and not independently verified.",
      created_at: "2026-07-16T00:00:00Z",
    },
  ],
  truth_warning:
    "Evidence linked here is private and not independently verified. Linking evidence does not verify your Passport, your profile, or a claim.",
};

function renderPanel() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PassportEvidencePanel />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function pageText(): string {
  return document.body.textContent || "";
}

describe("PassportEvidencePanel", () => {
  beforeEach(() => {
    getEvidencePassportSummary.mockReset();
  });

  it("renders Private evidence awareness with safe copy", async () => {
    getEvidencePassportSummary.mockResolvedValue(emptySummary);
    renderPanel();
    expect(
      await screen.findByText("Private evidence awareness"),
    ).toBeInTheDocument();
    expect(pageText()).toMatch(/private and not independently verified/i);
    expect(pageText()).toMatch(
      /does not verify your Passport, your profile, or a claim/i,
    );
  });

  it("shows empty state and Open Evidence Library link to /evidence", async () => {
    getEvidencePassportSummary.mockResolvedValue(emptySummary);
    renderPanel();
    expect(
      await screen.findByText(/No evidence-linked claims yet/i),
    ).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /Open Evidence Library/i });
    expect(link).toHaveAttribute("href", "/evidence");
  });

  it("renders linked evidence cards with safe labels and no download", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    renderPanel();
    expect(await screen.findByText("Python")).toBeInTheDocument();
    expect(screen.getByText(/Cert metadata/)).toBeInTheDocument();
    expect(screen.getAllByText("Not independently verified").length).toBeGreaterThan(
      0,
    );
    expect(pageText()).toMatch(/Linked as support material|supports/i);
    expect(pageText()).toMatch(/Private file attached/i);
    expect(screen.queryByRole("button", { name: /download/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /upload/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /verify/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /share|publish/i })).toBeNull();
    expect(document.querySelector('input[type="file"]')).toBeNull();
  });

  it("forbids unsafe trust wording", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    renderPanel();
    await waitFor(() => expect(getEvidencePassportSummary).toHaveBeenCalled());
    const text = pageText().toLowerCase();
    for (const forbidden of [
      "official",
      "trusted",
      "proof of truth",
      "verified credential",
      "verified document",
      "public credential",
      "wallet",
      "blockchain",
      "did",
      "verified passport",
    ]) {
      expect(text).not.toContain(forbidden);
    }
    // "verified" only inside "not independently verified"
    const withoutSafe = text.replace(/not independently verified/g, "");
    expect(withoutSafe).not.toContain("verified");
  });
});
