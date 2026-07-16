/**
 * EvidenceLibraryPage.test.tsx — 0053-F4/F6 private metadata + attachment UI.
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
  storage_uri: "local-evidence://11111111-1111-1111-1111-111111111111/11111111-1111-1111-1111-111111111111/abc.txt",
  content_hash: "a".repeat(64),
  mime_type: "text/plain",
  size_bytes: 12,
};

function selectEvidence(title = "Degree scan metadata") {
  fireEvent.click(screen.getByText(title));
}

describe("EvidenceLibraryPage F6 attachment UI", () => {
  beforeEach(() => {
    listEvidence.mockReset();
    createEvidenceMetadata.mockReset();
    getEvidenceMetadata.mockReset();
    uploadEvidenceAttachment.mockReset();
    downloadEvidenceAttachment.mockReset();
    listPlatformSubjects.mockReset();
    addToast.mockReset();
    listPlatformSubjects.mockResolvedValue([]);
    listEvidence.mockResolvedValue([]);
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
    expect(
      screen.getByText(/Parsing and review are not enabled yet/i),
    ).toBeInTheDocument();
  });

  it("keeps forbidden buttons absent and metadata save available", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /Evidence Library/i });
    expect(
      screen.queryByRole("button", { name: /verify evidence/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /submit proof/i }),
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
  });

  it("selected evidence shows attachment section with guidance", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByRole("region", { name: /Private attachment/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Max 5 MB/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Allowed types: PDF, PNG, JPEG, TXT, DOCX/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /This attaches a private file to the metadata record. It does not verify the evidence or any claim/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Attach private file/i }),
    ).toBeInTheDocument();
    expect(
      document.querySelector('input[type="file"]'),
    ).not.toBeNull();
  });

  it("file input is absent until an evidence record is selected", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    expect(document.querySelector('input[type="file"]')).toBeNull();
    selectEvidence();
    expect(
      await screen.findByTestId("evidence-attachment-input"),
    ).toBeInTheDocument();
  });

  it("blocks upload with no file before API call", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    fireEvent.click(screen.getByRole("button", { name: /Attach private file/i }));
    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "error",
          message: "Choose a private file to attach.",
        }),
      ),
    );
    expect(uploadEvidenceAttachment).not.toHaveBeenCalled();
  });

  it("blocks empty and too-large and disallowed MIME before API call", () => {
    const empty = new File([""], "empty.txt", { type: "text/plain" });
    Object.defineProperty(empty, "size", { value: 0 });
    expect(validatePrivateAttachmentFile(empty)).toMatch(/Empty/i);

    const large = new File(["x"], "big.txt", { type: "text/plain" });
    Object.defineProperty(large, "size", { value: 5 * 1024 * 1024 + 1 });
    expect(validatePrivateAttachmentFile(large)).toMatch(/5 MB/i);

    const bad = new File(["MZ"], "x.exe", { type: "application/x-msdownload" });
    expect(validatePrivateAttachmentFile(bad)).toMatch(/not allowed/i);

    const ok = new File(["hello"], "note.txt", { type: "text/plain" });
    expect(validatePrivateAttachmentFile(ok)).toBeNull();
  });

  it("upload sends file to API and refreshes list on success", async () => {
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

    await waitFor(() =>
      expect(uploadEvidenceAttachment).toHaveBeenCalledTimes(1),
    );
    expect(uploadEvidenceAttachment.mock.calls[0][0]).toBe(sampleRecord.id);
    expect(uploadEvidenceAttachment.mock.calls[0][1]).toBe(file);
    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith(
        expect.objectContaining({
          message:
            "Private file attached. This is still not independently verified.",
        }),
      ),
    );
    await waitFor(() => expect(listEvidence.mock.calls.length).toBeGreaterThan(1));
  });

  it("shows friendly duplicate attachment error", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    uploadEvidenceAttachment.mockRejectedValue({
      error: true,
      code: "CONFLICT",
      message: "duplicate evidence attachment is not allowed without replace",
      details: {},
    });
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    const input = await screen.findByTestId("evidence-attachment-input");
    const file = new File(["hello"], "note.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: /Attach private file/i }));
    expect(
      await screen.findByText(
        /This evidence already has an attachment. Replacement is not enabled yet/i,
      ),
    ).toBeInTheDocument();
  });

  it("shows download control when has_attachment is true and uses blob download", async () => {
    listEvidence.mockResolvedValue([attachedRecord]);
    downloadEvidenceAttachment.mockResolvedValue(
      new Blob(["hello"], { type: "text/plain" }),
    );
    const createObjectURL = vi.fn(() => "blob:local-only");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL,
      revokeObjectURL,
    });
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);

    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    expect(
      await screen.findByRole("button", { name: /Download private attachment/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/https?:\/\//i)).not.toBeInTheDocument();
    expect(
      screen.getByText(/Private internal reference \(not a public URL\)/i),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /Download private attachment/i }),
    );
    await waitFor(() =>
      expect(downloadEvidenceAttachment).toHaveBeenCalledWith(attachedRecord.id),
    );
    await waitFor(() => expect(createObjectURL).toHaveBeenCalled());
    await waitFor(() => expect(revokeObjectURL).toHaveBeenCalled());
    expect(document.body.textContent).not.toMatch(/https?:\/\/example/);
    clickSpy.mockRestore();
    vi.unstubAllGlobals();
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
    expect(payload).not.toHaveProperty("owner_user_id");
  });

  it("forbids unsafe trust wording except Not independently verified", async () => {
    listEvidence.mockResolvedValue([sampleRecord]);
    renderPage();
    await screen.findByText("Degree scan metadata");
    selectEvidence();
    await screen.findByRole("region", { name: /Private attachment/i });
    const text = document.body.textContent?.toLowerCase() ?? "";
    for (const forbidden of [
      "official",
      "trusted",
      "proof of truth",
      "verified document",
      "public credential",
      "wallet",
      "blockchain",
    ]) {
      expect(text).not.toContain(forbidden);
    }
    // Avoid bare DID token (word boundary).
    expect(text).not.toMatch(/\bdid\b/);
    expect(text).toContain("not independently verified");
    const withoutSafe = text.split("not independently verified").join("");
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
