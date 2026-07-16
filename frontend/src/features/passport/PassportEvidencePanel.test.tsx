/**
 * PassportEvidencePanel tests (0053-F8 / F11) — evidence awareness + review request UI.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import type {
  PassportEvidenceSummaryRead,
  ReviewRequestRead,
} from "@/types/api";

const getEvidencePassportSummary = vi.fn();
const listReviewRequests = vi.fn();
const createReviewRequest = vi.fn();
const cancelReviewRequest = vi.fn();

vi.mock("@/lib/api", () => ({
  evidenceApi: {
    getEvidencePassportSummary: (...args: unknown[]) =>
      getEvidencePassportSummary(...args),
  },
  reviewRequestApi: {
    listReviewRequests: (...args: unknown[]) => listReviewRequests(...args),
    createReviewRequest: (...args: unknown[]) => createReviewRequest(...args),
    cancelReviewRequest: (...args: unknown[]) => cancelReviewRequest(...args),
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

const requestedReview: ReviewRequestRead = {
  id: "dddddddd-dddd-dddd-dddd-dddddddddddd",
  subject_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
  claim_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  review_state: "requested",
  review_state_label: "Review requested",
  review_state_help_text:
    "A review was requested. This does not independently verify the claim.",
  reviewer_type: null,
  request_note: null,
  cancellation_reason: null,
  created_at: "2026-07-16T00:00:00Z",
  updated_at: "2026-07-16T00:00:00Z",
  cancelled_at: null,
  claim_verification_status: "unverified",
  claim_verification_label: "Not independently verified",
  warning:
    "A review request is not verification. Claim status changes require a future explicit review workflow.",
};

const cancelledReview: ReviewRequestRead = {
  ...requestedReview,
  id: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  review_state: "cancelled",
  review_state_label: "Review cancelled",
  review_state_help_text: "The review request was cancelled.",
  cancelled_at: "2026-07-16T01:00:00Z",
  updated_at: "2026-07-16T01:00:00Z",
};

function renderPanel() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
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

function assertSafeTrustWording(text: string) {
  const scrubbed = text
    .toLowerCase()
    .replace(/not independently verified/g, "")
    .replace(/does not independently verify/g, "")
    .replace(/requesting a review does not verify a claim/g, "")
    .replace(/does not verify your passport/g, "")
    .replace(/does not verify a claim/g, "")
    .replace(/this is not verification/g, "")
    .replace(/is not verification/g, "")
    .replace(/a review request is not verification/g, "")
    .replace(/a request is not verification/g, "")
    .replace(/request intake requires linked private evidence/g, "");
  for (const forbidden of [
    "official",
    "trusted",
    "proof of truth",
    "verified credential",
    "verified document",
    "public credential",
    "wallet",
    "blockchain",
    "verified passport",
    "verify claim",
    "verify passport",
  ]) {
    expect(scrubbed).not.toContain(forbidden);
  }
  expect(scrubbed).not.toMatch(/\bdid\b/);
  expect(scrubbed).not.toContain("verified");
}

describe("PassportEvidencePanel", () => {
  beforeEach(() => {
    getEvidencePassportSummary.mockReset();
    listReviewRequests.mockReset();
    createReviewRequest.mockReset();
    cancelReviewRequest.mockReset();
    listReviewRequests.mockResolvedValue([]);
  });

  it("renders Private evidence awareness with safe copy", async () => {
    getEvidencePassportSummary.mockResolvedValue(emptySummary);
    renderPanel();
    expect(
      await screen.findByText("Private evidence awareness"),
    ).toBeInTheDocument();
    expect(pageText()).toMatch(/private and not independently verified/i);
    expect(pageText()).toMatch(
      /Requesting a review does not verify a claim/i,
    );
  });

  it("shows intake requires linked private evidence copy on linked cards", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([]);
    renderPanel();
    expect(await screen.findByText("Python")).toBeInTheDocument();
    expect(pageText()).toMatch(
      /Request intake requires linked private evidence/i,
    );
    expect(pageText()).toMatch(/A request is not verification/i);
  });

  it("maps backend linked-evidence error to safe alert", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([]);
    createReviewRequest.mockRejectedValue({
      message:
        "A linked private evidence record is required before requesting review.",
    });
    renderPanel();
    await screen.findByRole("button", { name: "Request private review" });
    fireEvent.click(
      screen.getByRole("button", { name: "Request private review" }),
    );
    expect(
      await screen.findByText("Link private evidence before requesting review."),
    ).toBeInTheDocument();
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

  it("shows request private review when no active request", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([]);
    renderPanel();
    expect(await screen.findByText("Python")).toBeInTheDocument();
    expect(
      screen.getAllByText("Not independently verified").length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: "Request private review" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /verify claim/i }),
    ).toBeNull();
  });

  it("creates review request with claim_id and optional note", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([]);
    createReviewRequest.mockResolvedValue(requestedReview);
    renderPanel();
    await screen.findByRole("button", { name: "Request private review" });
    fireEvent.change(
      screen.getByLabelText(/Optional note for future review/i),
      { target: { value: "Please review privately" } },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Request private review" }),
    );
    await waitFor(() => expect(createReviewRequest).toHaveBeenCalledTimes(1));
    expect(createReviewRequest.mock.calls[0][0]).toEqual({
      claim_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      request_note: "Please review privately",
    });
    expect(
      await screen.findByText(/Review requested\. This is not verification\./i),
    ).toBeInTheDocument();
  });

  it("shows cancel for active requested review", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([requestedReview]);
    renderPanel();
    expect(await screen.findByText("Review requested")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel review request" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Request private review" }),
    ).toBeNull();
  });

  it("cancels review request with optional reason", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([requestedReview]);
    cancelReviewRequest.mockResolvedValue(cancelledReview);
    renderPanel();
    await screen.findByRole("button", { name: "Cancel review request" });
    fireEvent.change(
      screen.getByLabelText(/Optional cancellation reason/i),
      { target: { value: "Changed mind" } },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Cancel review request" }),
    );
    await waitFor(() => expect(cancelReviewRequest).toHaveBeenCalledTimes(1));
    expect(cancelReviewRequest.mock.calls[0][0]).toBe(
      "dddddddd-dddd-dddd-dddd-dddddddddddd",
    );
    expect(cancelReviewRequest.mock.calls[0][1]).toEqual({
      cancellation_reason: "Changed mind",
    });
    expect(
      await screen.findByText(
        /Claim remains not independently verified/i,
      ),
    ).toBeInTheDocument();
  });

  it("cancelled historical request is not shown as verified", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([cancelledReview]);
    renderPanel();
    expect(
      await screen.findByRole("button", { name: "Request private review" }),
    ).toBeInTheDocument();
    expect(pageText()).toMatch(/Review cancelled/i);
    expect(pageText()).toMatch(/not independently verified/i);
    assertSafeTrustWording(pageText());
  });

  it("forbids verify/approve/reject/share/upload/download controls", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([requestedReview]);
    renderPanel();
    await screen.findByText("Review requested");
    for (const name of [
      /verify claim/i,
      /verify passport/i,
      /^approve$/i,
      /^reject$/i,
      /publish/i,
      /share/i,
      /download/i,
      /upload/i,
    ]) {
      expect(screen.queryByRole("button", { name })).toBeNull();
    }
    expect(document.querySelector('input[type="file"]')).toBeNull();
  });

  it("forbids unsafe trust wording", async () => {
    getEvidencePassportSummary.mockResolvedValue(linkedSummary);
    listReviewRequests.mockResolvedValue([requestedReview]);
    renderPanel();
    await waitFor(() => expect(listReviewRequests).toHaveBeenCalled());
    assertSafeTrustWording(pageText());
  });
});
