/**
 * EvidenceLibraryPage.test.tsx — 0053-F4/F6/F7 private metadata, attachment, linking UI.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

const listEvidence = vi.fn();
const createEvidenceMetadata = vi.fn();
const getEvidenceMetadata = vi.fn();
const uploadEvidenceAttachment = vi.fn();
const downloadEvidenceAttachment = vi.fn();
const listLinkableEvidenceClaims = vi.fn();
const listEvidenceClaimLinks = vi.fn();
const linkEvidenceToClaim = vi.fn();
const listPlatformSubjects = vi.fn();
const addToast = vi.fn();

vi.mock("@/lib/api", () => ({
  evidenceApi: {
    listEvidence: (...args: unknown[]) => listEvidence(...args),
    createEvidenceMetadata: (...args: unknown[]) => createEvidenceMetadata(...args),
    getEvidenceMetadata: (...args: unknown[]) => getEvidenceMetadata(...args),
    uploadEvidenceAttachment: (...args: unknown[]) =>
      uploadEvidenceAttachment(...args),
    downloadEvidenceAttachment: (...args: unknown[]) =>
      downloadEvidenceAttachment(...args),
    listLinkableEvidenceClaims: (...args: unknown[]) =>
      listLinkableEvidenceClaims(...args),
    listEvidenceClaimLinks: (...args: unknown[]) =>
      listEvidenceClaimLinks(...args),
    linkEvidenceToClaim: (...args: unknown[]) => linkEvidenceToClaim(...args),
  },
  platformApi: {
    listPlatformSubjects: (...args: unknown[]) => listPlatformSubjects(...args),
  },
}));

vi.mock("@/store/ui", () => ({
  useUIStore: () => ({ addToast }),
}));

import EvidenceLibraryPage, {
  validatePrivateAttachmentFile,
} from "./EvidenceLibraryPage";

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
  has_attachment: false,
  evidence_kind_label: "Transcript material",
  privacy_label: "Private",
  truth_warning:
    "Evidence material linked to a claim is private metadata only. A link is not independent review and does not change verification status.",
  created_at: "2026-07-16T10:00:00Z",
  updated_at: "2026-07-16T10:00:00Z",
};

const attachedRecord = {
  ...sampleRecord,
  has_attachment: true,
  storage_uri:
    "local-evidence://11111111-1111-1111-1111-111111111111/11111111-1111-1111-1111-111111111111/abc.txt",
  content_hash: "a".repeat(64),
  mime_type: "text/plain",
  size_bytes: 12,
  attachment_safety_status: "scan_not_available",
  attachment_safety_label: "Scan not available",
  attachment_safety_warning:
    "Private attachments are stored but not malware-scanned, parsed, reviewed, or verified in this version.",
};

const sampleClaim = {
  id: "22222222-2222-2222-2222-222222222222",
  subject_id: "33333333-3333-3333-3333-333333333333",
  claim_kind: "skill",
  claim_key: "python",
  claim_value: "Python",
  claim_origin: "user_asserted",
  support_status: "not_provided",
  support_label: "Not supported yet",
  verification_status: "unverified",
  verification_label: "Not independently verified",
  truth_warning:
    "A source or snapshot link is not verification. This claim is private and not independently verified.",
  created_at: "2026-07-16T09:00:00Z",
};

const sampleLink = {
  id: "44444444-4444-4444-4444-444444444444",
  claim_id: sampleClaim.id,
  evidence_id: sampleRecord.id,
  link_role: "supports",
  link_role_label: "Linked as support material",
  created_at: "2026-07-16T11:00:00Z",
  claim_kind: "skill",
  claim_key: "python",
  claim_value: "Python",
  claim_support_status: "not_provided",
  claim_support_label: "Not supported yet",
  claim_verification_status: "unverified",
  claim_verification_label: "Not independently verified",
  truth_warning: sampleRecord.truth_warning,
};

function selectEvidence(title = "Degree scan metadata") {
  fireEvent.click(screen.getByText(title));
}

describe("EvidenceLibraryPage F6/F7 boundary", () => {
  beforeEach(() => {
    listEvidence.mockReset();
    createEvidenceMetadata.mockReset();
    getEvidenceMetadata.mockReset();
    uploadEvidenceAttachment.mockReset();
    downloadEvidenceAttachment.mockReset();
    listLinkableEvidenceClaims.mockReset();
    listEvidenceClaimLinks.mockReset();
    linkEvidenceToClaim.mockReset();
    listPlatformSubjects.mockReset();
    addToast.mockReset();
    listPlatformSubjects.mockResolvedValue([]);
    listEvidence.mockResolvedValue([]);
    listLinkableEvidenceClaims.mockResolvedValue([]);
    listEvidenceClaimLinks.mockResolvedValue([]);
  });

  it("renders Evidence Library with private / not independently verified copy", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: /Evidence Library/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Private evidence library/i)).toBeInTheDocument();
    expect(
      screen.getAllByText(/not independently verified/i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByText(/Uploading a file does not verify a claim/i),
    ).toBeInTheDocument();
  });

  it("keeps forbidden buttons absent", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /Evidence Library/i });
    expect(
      screen.queryByRole("button", { name: /verify claim|verify evidence/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /submit proof/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /share|publish/i }),
    ).not.toBeInTheDocument();
  });

  it("shows empty evidence state", async () => {
    renderPage();
    expect(
      await screen.findByText(/No evidence metadata saved yet/i),
    ).toBeInTheDocument();
  });

  it("selected evidence shows attachment section with attach control", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByRole("button", { name: /Attach private file/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Max 5 MB/i)).toBeInTheDocument();
  });

  it("blocks empty/too-large/disallowed MIME before API call", () => {
    const empty = new File([""], "empty.txt", { type: "text/plain" });
    Object.defineProperty(empty, "size", { value: 0 });
    expect(validatePrivateAttachmentFile(empty)).toMatch(/Empty/i);
    const large = new File(["x"], "big.txt", { type: "text/plain" });
    Object.defineProperty(large, "size", { value: 5 * 1024 * 1024 + 1 });
    expect(validatePrivateAttachmentFile(large)).toMatch(/5 MB/i);
    const bad = new File(["MZ"], "x.exe", { type: "application/x-msdownload" });
    expect(validatePrivateAttachmentFile(bad)).toMatch(/not allowed/i);
  });

  it("upload sends file to API on success path", async () => {
    listEvidence
      .mockResolvedValueOnce([sampleRecord])
      .mockResolvedValueOnce([attachedRecord]);
    uploadEvidenceAttachment.mockResolvedValue(attachedRecord);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    const input = await screen.findByTestId("evidence-attachment-input");
    const file = new File(["hello-evidence"], "note.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: /Attach private file/i }));
    await waitFor(() => expect(uploadEvidenceAttachment).toHaveBeenCalledTimes(1));
  });

  it("shows attachment safety warning for attached records", async () => {
    listEvidence.mockResolvedValue([attachedRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    const text = document.body.textContent || "";
    expect(text).toMatch(/Private attachment stored/i);
    expect(text).toMatch(/Not malware-scanned/i);
    expect(text).toMatch(/parsed, reviewed, or verified/i);
    expect(text).toMatch(/Scan not available/i);
    expect(
      screen.queryByRole("button", { name: /^Scan$/i }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: /^Parse$/i }),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: /^OCR$/i })).toBeNull();
    expect(
      screen.queryByRole("button", { name: /^AI review$/i }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: /^Verify$/i }),
    ).toBeNull();
  });

  it("download control uses blob API without public URL", async () => {
    listEvidence.mockResolvedValue([attachedRecord]);
    downloadEvidenceAttachment.mockResolvedValue(
      new Blob(["hello"], { type: "text/plain" }),
    );
    const createObjectURL = vi.fn(() => "blob:local-only");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { ...URL, createObjectURL, revokeObjectURL });
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    fireEvent.click(
      await screen.findByRole("button", { name: /Download private attachment/i }),
    );
    await waitFor(() =>
      expect(downloadEvidenceAttachment).toHaveBeenCalledWith(attachedRecord.id),
    );
    clickSpy.mockRestore();
    vi.unstubAllGlobals();
  });

  it("selected evidence shows claim linking section and safe copy", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByRole("heading", {
        name: /Link this evidence to a claim/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /This creates a private link between the selected evidence and one of your claims. It does not verify the claim/i,
      ),
    ).toBeInTheDocument();
  });

  it("shows empty claims state", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    listLinkableEvidenceClaims.mockResolvedValue([]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByText(/No private claims are available to link yet/i),
    ).toBeInTheDocument();
  });

  it("loads claims, selects role, and links via API", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    listLinkableEvidenceClaims.mockResolvedValue([sampleClaim]);
    listEvidenceClaimLinks.mockResolvedValue([]);
    linkEvidenceToClaim.mockResolvedValue({
      id: sampleLink.id,
      claim_id: sampleClaim.id,
      evidence_id: sampleRecord.id,
      link_role: "supports",
      link_role_label: "Linked as support material",
      created_at: sampleLink.created_at,
      truth_warning: sampleRecord.truth_warning,
      claim_support_status: "not_provided",
      claim_verification_status: "unverified",
      claim_support_label: "Not supported yet",
      claim_verification_label: "Not independently verified",
    });
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    const claimSelect = await screen.findByLabelText(/Claim to link/i);
    expect(claimSelect).toHaveTextContent(/skill: Python/i);
    expect(claimSelect).toHaveTextContent(/Not independently verified/i);
    fireEvent.change(claimSelect, { target: { value: sampleClaim.id } });
    const roleSelect = screen.getByLabelText(/Link role/i);
    expect(roleSelect).toHaveTextContent(/Supports/);
    expect(roleSelect).toHaveTextContent(/Contests/);
    expect(roleSelect).toHaveTextContent(/Context/);
    fireEvent.change(roleSelect, { target: { value: "supports" } });
    fireEvent.click(
      screen.getByRole("button", { name: /Link evidence to claim/i }),
    );
    await waitFor(() => expect(linkEvidenceToClaim).toHaveBeenCalledTimes(1));
    expect(linkEvidenceToClaim.mock.calls[0][0]).toEqual({
      evidence_id: sampleRecord.id,
      claim_id: sampleClaim.id,
      link_role: "supports",
    });
    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith(
        expect.objectContaining({
          message:
            "Evidence linked. This claim is still not independently verified.",
        }),
      ),
    );
  });

  it("shows friendly duplicate link error", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    listLinkableEvidenceClaims.mockResolvedValue([sampleClaim]);
    linkEvidenceToClaim.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "duplicate claim/evidence link is not allowed",
      details: {},
    });
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    fireEvent.change(await screen.findByLabelText(/Claim to link/i), {
      target: { value: sampleClaim.id },
    });
    fireEvent.click(
      screen.getByRole("button", { name: /Link evidence to claim/i }),
    );
    expect(
      await screen.findByText(/This evidence is already linked to that claim/i),
    ).toBeInTheDocument();
  });

  it("displays existing links with safe labels", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    listLinkableEvidenceClaims.mockResolvedValue([sampleClaim]);
    listEvidenceClaimLinks.mockResolvedValue([sampleLink]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByText(/Existing links for this evidence/i),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/Linked as support material/i),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/skill: Python/i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Not independently verified/i).length,
    ).toBeGreaterThan(0);
  });

  it("forbids unsafe trust wording except Not independently verified", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    listLinkableEvidenceClaims.mockResolvedValue([sampleClaim]);
    listEvidenceClaimLinks.mockResolvedValue([sampleLink]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    await screen.findByRole("heading", {
      name: /Link this evidence to a claim/i,
    });
    const text = document.body.textContent?.toLowerCase() ?? "";
    for (const forbidden of [
      "official",
      "trusted",
      "proof of truth",
      "verified credential",
      "verified document",
      "public credential",
      "wallet",
      "blockchain",
      "safe file",
      "trusted file",
    ]) {
      expect(text).not.toContain(forbidden);
    }
    expect(text).not.toMatch(/\bdid\b/);
    expect(text).toContain("not independently verified");
    const withoutSafe = text
      .split("not independently verified")
      .join("")
      .split("or verified in this version")
      .join("")
      .split("reviewed, or verified")
      .join("");
    expect(withoutSafe).not.toContain("verified");
  });
});
