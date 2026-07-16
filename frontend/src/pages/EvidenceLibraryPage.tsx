/**
 * EvidenceLibraryPage.tsx
 * =======================
 * Private Evidence Library (0053-F4/F6): metadata create/list + private
 * attachment upload/download via F5 APIs. No verification, public sharing,
 * OCR/parsing, or claim linker.
 */

import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Info, Library } from "lucide-react";
import { evidenceApi, platformApi } from "../lib/api";
import type {
  ApiError,
  EvidenceCreateRequest,
  EvidenceKind,
  EvidenceLinkRole,
  EvidencePrivacyClass,
  EvidenceRead,
} from "../types/api";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";

const EVIDENCE_KINDS: EvidenceKind[] = [
  "document",
  "certificate",
  "transcript",
  "portfolio",
  "assessment",
  "reference",
  "source_snapshot",
  "other",
];

const PRIVACY_CLASSES: EvidencePrivacyClass[] = [
  "private",
  "sensitive",
  "restricted",
];

const LINK_ROLES: { value: EvidenceLinkRole; label: string }[] = [
  { value: "supports", label: "Supports" },
  { value: "contests", label: "Contests" },
  { value: "context", label: "Context" },
];

const MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024;

const ALLOWED_MIME_TYPES = new Set([
  "application/pdf",
  "image/png",
  "image/jpeg",
  "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);

const ALLOWED_EXTENSIONS = new Set([
  ".pdf",
  ".png",
  ".jpg",
  ".jpeg",
  ".txt",
  ".docx",
]);

const FILE_ACCEPT =
  ".pdf,.png,.jpg,.jpeg,.txt,.docx,application/pdf,image/png,image/jpeg,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function shortId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 8)}…` : id;
}

function shortHash(hash: string | null | undefined): string {
  if (!hash) return "—";
  return hash.length > 16 ? `${hash.slice(0, 12)}…` : hash;
}

function formatBytes(size: number | null | undefined): string {
  if (size == null) return "—";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function fileExtension(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}

/** Client-side guards before calling the F5 upload API. */
export function validatePrivateAttachmentFile(file: File | null): string | null {
  if (!file) return "Choose a private file to attach.";
  if (file.size === 0) return "Empty files cannot be attached.";
  if (file.size > MAX_ATTACHMENT_BYTES) {
    return "File exceeds the 5 MB limit.";
  }
  const mime = (file.type || "").split(";", 1)[0].trim().toLowerCase();
  const ext = fileExtension(file.name);
  const mimeOk = mime ? ALLOWED_MIME_TYPES.has(mime) : false;
  const extOk = ALLOWED_EXTENSIONS.has(ext);
  if (!mimeOk && !extOk) {
    return "File type is not allowed. Use PDF, PNG, JPEG, TXT, or DOCX.";
  }
  if (mime && !ALLOWED_MIME_TYPES.has(mime)) {
    return "File type is not allowed. Use PDF, PNG, JPEG, TXT, or DOCX.";
  }
  return null;
}

function hasAttachment(row: EvidenceRead): boolean {
  return Boolean(row.has_attachment || row.storage_uri);
}

const emptyForm = {
  title: "",
  evidence_kind: "document" as EvidenceKind,
  privacy_class: "private" as EvidencePrivacyClass,
  subject_id: "",
  storage_uri: "",
  content_hash: "",
  mime_type: "",
  size_bytes: "",
};

export default function EvidenceLibraryPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);
  const [linkClaimId, setLinkClaimId] = useState("");
  const [linkRole, setLinkRole] = useState<EvidenceLinkRole>("supports");
  const [linkError, setLinkError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const listQuery = useQuery({
    queryKey: ["evidence", "list"],
    queryFn: () => evidenceApi.listEvidence(),
  });

  const subjectsQuery = useQuery({
    queryKey: ["platform", "subjects"],
    queryFn: () => platformApi.listPlatformSubjects(),
  });

  const linkableClaimsQuery = useQuery({
    queryKey: ["evidence", "linkable-claims"],
    queryFn: () => evidenceApi.listLinkableEvidenceClaims(),
  });

  const evidenceLinksQuery = useQuery({
    queryKey: ["evidence", "links", selectedId],
    queryFn: () => evidenceApi.listEvidenceClaimLinks(selectedId!),
    enabled: Boolean(selectedId),
  });

  const createMutation = useMutation({
    mutationFn: (payload: EvidenceCreateRequest) =>
      evidenceApi.createEvidenceMetadata(payload),
    onSuccess: (row) => {
      addToast({ type: "success", message: "Evidence metadata saved." });
      setForm(emptyForm);
      setSelectedId(row.id);
      qc.invalidateQueries({ queryKey: ["evidence", "list"] });
    },
    onError: (err: ApiError) => {
      addToast({
        type: "error",
        message: err.message || "Could not save evidence metadata.",
      });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ evidenceId, file }: { evidenceId: string; file: File }) =>
      evidenceApi.uploadEvidenceAttachment(evidenceId, file),
    onSuccess: (row) => {
      addToast({
        type: "success",
        message:
          "Private file attached. This is still not independently verified.",
      });
      setSelectedFile(null);
      setAttachError(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setSelectedId(row.id);
      qc.invalidateQueries({ queryKey: ["evidence", "list"] });
    },
    onError: (err: ApiError) => {
      const message = (err.message || "").toLowerCase();
      const duplicate =
        err.code === "CONFLICT" ||
        message.includes("duplicate") ||
        message.includes("already has");
      const friendly = duplicate
        ? "This evidence already has an attachment. Replacement is not enabled yet."
        : err.message || "Could not attach private file.";
      setAttachError(friendly);
      addToast({ type: "error", message: friendly });
    },
  });

  const downloadMutation = useMutation({
    mutationFn: async (row: EvidenceRead) => {
      const blob = await evidenceApi.downloadEvidenceAttachment(row.id);
      return { blob, row };
    },
    onSuccess: ({ blob, row }) => {
      if (!(blob instanceof Blob) || blob.size === 0) {
        addToast({ type: "error", message: "Attachment download was empty." });
        return;
      }
      // Local object URL for immediate download only — never stored as public URL.
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = objectUrl;
      a.download = `evidence-${row.id.slice(0, 8)}-private`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
      addToast({ type: "success", message: "Private attachment downloaded." });
    },
    onError: (err: ApiError) => {
      addToast({
        type: "error",
        message: err.message || "Could not download private attachment.",
      });
    },
  });

  const linkMutation = useMutation({
    mutationFn: () =>
      evidenceApi.linkEvidenceToClaim({
        evidence_id: selectedId!,
        claim_id: linkClaimId,
        link_role: linkRole,
      }),
    onSuccess: () => {
      addToast({
        type: "success",
        message:
          "Evidence linked. This claim is still not independently verified.",
      });
      setLinkError(null);
      qc.invalidateQueries({ queryKey: ["evidence", "links", selectedId] });
    },
    onError: (err: ApiError) => {
      const message = (err.message || "").toLowerCase();
      const duplicate =
        err.code === "CONFLICT" || message.includes("duplicate");
      const friendly = duplicate
        ? "This evidence is already linked to that claim."
        : err.message || "Could not link evidence to claim.";
      setLinkError(friendly);
      addToast({ type: "error", message: friendly });
    },
  });

  const selected: EvidenceRead | undefined = useMemo(
    () => listQuery.data?.find((row) => row.id === selectedId),
    [listQuery.data, selectedId],
  );

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const title = form.title.trim();
    if (!title) {
      addToast({ type: "error", message: "Title is required." });
      return;
    }
    const payload: EvidenceCreateRequest = {
      title,
      evidence_kind: form.evidence_kind,
      privacy_class: form.privacy_class,
      subject_id: form.subject_id.trim() || null,
      storage_uri: form.storage_uri.trim() || null,
      content_hash: form.content_hash.trim() || null,
      mime_type: form.mime_type.trim() || null,
      size_bytes:
        form.size_bytes.trim() === ""
          ? null
          : Number.parseInt(form.size_bytes.trim(), 10),
    };
    if (payload.size_bytes != null && Number.isNaN(payload.size_bytes)) {
      addToast({ type: "error", message: "size_bytes must be a whole number." });
      return;
    }
    // Never send owner_user_id — ownership comes from auth only.
    createMutation.mutate(payload);
  }

  function onAttach() {
    if (!selected) return;
    const validationError = validatePrivateAttachmentFile(selectedFile);
    if (validationError) {
      setAttachError(validationError);
      addToast({ type: "error", message: validationError });
      return;
    }
    setAttachError(null);
    uploadMutation.mutate({ evidenceId: selected.id, file: selectedFile! });
  }

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "0.5rem 0 2rem" }}>
      <header style={{ marginBottom: "1.75rem" }}>
        <p
          style={{
            fontSize: "0.75rem",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "var(--text-secondary)",
            marginBottom: "0.35rem",
          }}
        >
          Private evidence library
        </p>
        <h1
          style={{
            fontFamily: "var(--font-heading)",
            fontSize: "1.75rem",
            fontWeight: 700,
            marginBottom: "0.5rem",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <Library size={28} aria-hidden />
          Evidence Library
        </h1>
        <p style={{ color: "var(--text-secondary)", maxWidth: 720 }}>
          Private metadata and private file attachments. Evidence is not
          independently verified. Uploading a file does not verify a claim.
          Parsing and review are not enabled yet.
        </p>
      </header>

      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
            This library stores private evidence metadata and optional private
            file attachments that may later support career claims. CareerKundi
            does not make evidence public, run OCR/parsing, or treat an upload as
            verification.
          </p>
          <p
            style={{
              marginTop: "0.75rem",
              display: "flex",
              gap: "0.5rem",
              alignItems: "flex-start",
              color: "var(--text-secondary)",
              fontSize: "0.9rem",
            }}
          >
            <Info size={16} style={{ marginTop: 2, flexShrink: 0 }} aria-hidden />
            <span>
              Evidence-linked or source-linked metadata does not mean a claim is
              independently reviewed. Status remains: Not independently verified.
            </span>
          </p>
        </CardContent>
      </Card>

      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <CardHeader>
          <CardTitle>Create evidence metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} noValidate>
            <div
              style={{
                display: "grid",
                gap: "0.85rem",
                gridTemplateColumns: "1fr 1fr",
              }}
            >
              <div style={{ gridColumn: "1 / -1" }}>
                <Input
                  label="Title"
                  value={form.title}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, title: e.target.value }))
                  }
                  required
                  fullWidth
                  placeholder="e.g. Degree transcript reference"
                />
              </div>

              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  Evidence kind
                </span>
                <select
                  value={form.evidence_kind}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      evidence_kind: e.target.value as EvidenceKind,
                    }))
                  }
                  style={{
                    padding: "0.65rem 0.75rem",
                    borderRadius: 10,
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-overlay)",
                    color: "var(--text-primary)",
                  }}
                >
                  {EVIDENCE_KINDS.map((kind) => (
                    <option key={kind} value={kind}>
                      {kind}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  Privacy class
                </span>
                <select
                  value={form.privacy_class}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      privacy_class: e.target.value as EvidencePrivacyClass,
                    }))
                  }
                  style={{
                    padding: "0.65rem 0.75rem",
                    borderRadius: 10,
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-overlay)",
                    color: "var(--text-primary)",
                  }}
                >
                  {PRIVACY_CLASSES.map((privacy) => (
                    <option key={privacy} value={privacy}>
                      {privacy}
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  Subject (optional)
                </span>
                <select
                  value={form.subject_id}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, subject_id: e.target.value }))
                  }
                  style={{
                    padding: "0.65rem 0.75rem",
                    borderRadius: 10,
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-overlay)",
                    color: "var(--text-primary)",
                  }}
                >
                  <option value="">None</option>
                  {(subjectsQuery.data ?? []).map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {shortId(subject.id)}
                    </option>
                  ))}
                </select>
              </label>

              <Input
                label="Storage URI (metadata/reference only)"
                value={form.storage_uri}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, storage_uri: e.target.value }))
                }
                fullWidth
                hint="Optional reference string. Prefer attaching a private file below after saving."
                placeholder="e.g. future://attachment-ref"
              />
              <Input
                label="Content hash (optional)"
                value={form.content_hash}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, content_hash: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="MIME type (optional)"
                value={form.mime_type}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, mime_type: e.target.value }))
                }
                fullWidth
              />
              <Input
                label="Size bytes (optional)"
                value={form.size_bytes}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, size_bytes: e.target.value }))
                }
                fullWidth
                inputMode="numeric"
              />
            </div>

            <div style={{ marginTop: "1rem" }}>
              <Button
                type="submit"
                variant="primary"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? "Saving…" : "Save evidence metadata"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.1fr 0.9fr",
          gap: "1.25rem",
          marginBottom: "1.25rem",
        }}
      >
        <Card padding="lg">
          <CardHeader>
            <CardTitle>Saved evidence metadata</CardTitle>
          </CardHeader>
          <CardContent>
            {listQuery.isLoading ? (
              <Spinner />
            ) : listQuery.isError ? (
              <p style={{ color: "var(--text-secondary)" }}>
                Could not load evidence metadata.
              </p>
            ) : !listQuery.data?.length ? (
              <p style={{ color: "var(--text-secondary)" }}>
                No evidence metadata saved yet.
              </p>
            ) : (
              <ul
                style={{
                  listStyle: "none",
                  padding: 0,
                  margin: 0,
                  display: "grid",
                  gap: "0.75rem",
                }}
              >
                {listQuery.data.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedId(row.id);
                        setAttachError(null);
                        setSelectedFile(null);
                        setLinkError(null);
                        setLinkClaimId("");
                        setLinkRole("supports");
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "0.9rem 1rem",
                        borderRadius: 12,
                        border:
                          selectedId === row.id
                            ? "1px solid var(--accent, #8B5CF6)"
                            : "1px solid var(--border-subtle)",
                        background: "var(--bg-overlay)",
                        cursor: "pointer",
                        color: "var(--text-primary)",
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>{row.title}</div>
                      <div
                        style={{
                          fontSize: "0.8rem",
                          color: "var(--text-secondary)",
                          marginTop: 4,
                        }}
                      >
                        {row.evidence_kind_label} · {row.privacy_label}
                        {row.subject_id
                          ? ` · subject ${shortId(row.subject_id)}`
                          : ""}
                        {hasAttachment(row) ? " · Private attachment" : ""}
                      </div>
                      {hasAttachment(row) && (
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "var(--text-muted)",
                            marginTop: 6,
                          }}
                        >
                          Private attachment stored. Not malware-scanned,
                          parsed, reviewed, or verified.
                        </div>
                      )}
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                          marginTop: 6,
                        }}
                      >
                        {row.truth_warning}
                      </div>
                      <div
                        style={{
                          fontSize: "0.7rem",
                          color: "var(--text-muted)",
                          marginTop: 4,
                        }}
                      >
                        {formatDate(row.created_at)}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card padding="lg">
          <CardHeader>
            <CardTitle>Selected record</CardTitle>
          </CardHeader>
          <CardContent>
            {!selected ? (
              <p style={{ color: "var(--text-secondary)" }}>
                Select a record to view private metadata and attachment controls.
              </p>
            ) : (
              <div style={{ display: "grid", gap: "0.55rem", fontSize: "0.9rem" }}>
                <div>
                  <strong>{selected.title}</strong>
                </div>
                <div>Kind: {selected.evidence_kind_label}</div>
                <div>Privacy: {selected.privacy_label}</div>
                <div>
                  Subject:{" "}
                  {selected.subject_id ? shortId(selected.subject_id) : "None"}
                </div>
                <div>
                  Source / snapshot:{" "}
                  {selected.source_id || selected.snapshot_id
                    ? [
                        selected.source_id
                          ? `source ${shortId(selected.source_id)}`
                          : null,
                        selected.snapshot_id
                          ? `snapshot ${shortId(selected.snapshot_id)}`
                          : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")
                    : "None"}
                </div>
                <div>
                  Has attachment: {hasAttachment(selected) ? "yes" : "no"}
                </div>
                <div>MIME type: {selected.mime_type || "—"}</div>
                <div>Size: {formatBytes(selected.size_bytes)}</div>
                <div title={selected.content_hash || undefined}>
                  Content hash: {shortHash(selected.content_hash)}
                </div>
                <div>
                  Storage URI:{" "}
                  {selected.storage_uri
                    ? "Private internal reference (not a public URL)"
                    : "None"}
                </div>
                <div style={{ color: "var(--text-secondary)", marginTop: 4 }}>
                  {selected.truth_warning}
                </div>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                  Not independently verified
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  Created {formatDate(selected.created_at)}
                </div>

                <section
                  aria-label="Private attachment"
                  style={{
                    marginTop: "0.85rem",
                    paddingTop: "0.85rem",
                    borderTop: "1px solid var(--border-subtle)",
                    display: "grid",
                    gap: "0.65rem",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>Private attachment</div>
                  <p
                    style={{
                      color: "var(--text-secondary)",
                      fontSize: "0.85rem",
                      lineHeight: 1.5,
                      margin: 0,
                    }}
                  >
                    This attaches a private file to the metadata record. It does
                    not verify the evidence or any claim. Allowed types: PDF,
                    PNG, JPEG, TXT, DOCX. Max 5 MB. Parsing and review are not
                    enabled yet.
                  </p>

                  {!hasAttachment(selected) ? (
                    <>
                      <label
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: 6,
                          fontSize: "0.85rem",
                        }}
                      >
                        <span style={{ fontWeight: 600 }}>Choose private file</span>
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept={FILE_ACCEPT}
                          data-testid="evidence-attachment-input"
                          onChange={(e) => {
                            const file = e.target.files?.[0] ?? null;
                            setSelectedFile(file);
                            setAttachError(
                              file ? validatePrivateAttachmentFile(file) : null,
                            );
                          }}
                        />
                      </label>
                      {selectedFile ? (
                        <div
                          style={{
                            fontSize: "0.8rem",
                            color: "var(--text-secondary)",
                          }}
                        >
                          Selected: {selectedFile.name} (
                          {formatBytes(selectedFile.size)})
                        </div>
                      ) : null}
                      {attachError ? (
                        <div
                          role="alert"
                          style={{ color: "var(--danger, #b91c1c)", fontSize: "0.85rem" }}
                        >
                          {attachError}
                        </div>
                      ) : null}
                      <Button
                        type="button"
                        variant="primary"
                        disabled={uploadMutation.isPending}
                        onClick={onAttach}
                      >
                        {uploadMutation.isPending
                          ? "Attaching…"
                          : "Attach private file"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "0.85rem",
                          color: "var(--text-secondary)",
                        }}
                      >
                        Attached file stored privately. Replacement is not
                        enabled yet.
                      </p>
                      <p
                        style={{
                          margin: 0,
                          fontSize: "0.8rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        Private attachment stored. Not malware-scanned, parsed,
                        reviewed, or verified.
                      </p>
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={downloadMutation.isPending}
                        onClick={() => downloadMutation.mutate(selected)}
                      >
                        {downloadMutation.isPending
                          ? "Downloading…"
                          : "Download private attachment"}
                      </Button>
                    </>
                  )}
                </section>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <CardHeader>
          <CardTitle>Link this evidence to a claim</CardTitle>
        </CardHeader>
        <CardContent>
          {!selected ? (
            <p style={{ color: "var(--text-secondary)" }}>
              Select an evidence record above to link it to one of your private
              claims.
            </p>
          ) : (
            <div style={{ display: "grid", gap: "0.85rem" }}>
              <p
                style={{
                  color: "var(--text-secondary)",
                  lineHeight: 1.55,
                  margin: 0,
                }}
              >
                This creates a private link between the selected evidence and one
                of your claims. It does not verify the claim.
              </p>

              {linkableClaimsQuery.isLoading ? (
                <Spinner />
              ) : linkableClaimsQuery.isError ? (
                <p style={{ color: "var(--text-secondary)", margin: 0 }}>
                  Could not load private claims.
                </p>
              ) : !linkableClaimsQuery.data?.length ? (
                <p style={{ color: "var(--text-secondary)", margin: 0 }}>
                  No private claims are available to link yet.
                </p>
              ) : (
                <>
                  <label
                    style={{ display: "flex", flexDirection: "column", gap: 6 }}
                  >
                    <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                      Claim
                    </span>
                    <select
                      aria-label="Claim to link"
                      value={linkClaimId}
                      onChange={(e) => setLinkClaimId(e.target.value)}
                      style={{
                        padding: "0.65rem 0.75rem",
                        borderRadius: 10,
                        border: "1px solid var(--border-subtle)",
                        background: "var(--bg-overlay)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <option value="">Select a private claim</option>
                      {linkableClaimsQuery.data.map((claim) => (
                        <option key={claim.id} value={claim.id}>
                          {claim.claim_kind}: {claim.claim_value} ·{" "}
                          {claim.support_label} · {claim.verification_label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label
                    style={{ display: "flex", flexDirection: "column", gap: 6 }}
                  >
                    <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                      Link role
                    </span>
                    <select
                      aria-label="Link role"
                      value={linkRole}
                      onChange={(e) =>
                        setLinkRole(e.target.value as EvidenceLinkRole)
                      }
                      style={{
                        padding: "0.65rem 0.75rem",
                        borderRadius: 10,
                        border: "1px solid var(--border-subtle)",
                        background: "var(--bg-overlay)",
                        color: "var(--text-primary)",
                      }}
                    >
                      {LINK_ROLES.map((role) => (
                        <option key={role.value} value={role.value}>
                          {role.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  {linkError ? (
                    <div
                      role="alert"
                      style={{
                        color: "var(--danger, #b91c1c)",
                        fontSize: "0.85rem",
                      }}
                    >
                      {linkError}
                    </div>
                  ) : null}

                  <Button
                    type="button"
                    variant="primary"
                    disabled={linkMutation.isPending || !linkClaimId}
                    onClick={() => {
                      if (!selectedId || !linkClaimId) {
                        setLinkError("Choose a private claim to link.");
                        return;
                      }
                      linkMutation.mutate();
                    }}
                  >
                    {linkMutation.isPending
                      ? "Linking…"
                      : "Link evidence to claim"}
                  </Button>
                </>
              )}

              <div
                style={{
                  marginTop: "0.5rem",
                  paddingTop: "0.85rem",
                  borderTop: "1px solid var(--border-subtle)",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: "0.5rem" }}>
                  Existing links for this evidence
                </div>
                {evidenceLinksQuery.isLoading ? (
                  <Spinner />
                ) : !evidenceLinksQuery.data?.length ? (
                  <p
                    style={{
                      color: "var(--text-secondary)",
                      margin: 0,
                      fontSize: "0.85rem",
                    }}
                  >
                    No claim links yet for this evidence.
                  </p>
                ) : (
                  <ul
                    style={{
                      listStyle: "none",
                      padding: 0,
                      margin: 0,
                      display: "grid",
                      gap: "0.55rem",
                    }}
                  >
                    {evidenceLinksQuery.data.map((link) => (
                      <li
                        key={link.id}
                        style={{
                          padding: "0.7rem 0.85rem",
                          borderRadius: 10,
                          border: "1px solid var(--border-subtle)",
                          background: "var(--bg-overlay)",
                          fontSize: "0.85rem",
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>
                          {link.claim_kind}: {link.claim_value}
                        </div>
                        <div style={{ color: "var(--text-secondary)" }}>
                          {link.link_role_label} · {link.claim_support_label} ·{" "}
                          {link.claim_verification_label}
                        </div>
                        <div
                          style={{
                            color: "var(--text-muted)",
                            marginTop: 4,
                            fontSize: "0.75rem",
                          }}
                        >
                          {link.truth_warning}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card padding="lg">
        <CardHeader>
          <CardTitle>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <Archive size={18} aria-hidden />
              Attachment safety notes
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
            Private attachment storage is enabled for owner-only upload and
            download. Private attachments are stored but not malware-scanned,
            parsed, reviewed, or verified in this version. OCR, public sharing,
            and verification workflows are not enabled yet. Scan status: Scan
            not available.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
