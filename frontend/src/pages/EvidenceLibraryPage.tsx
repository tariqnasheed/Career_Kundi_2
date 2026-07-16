/**
 * EvidenceLibraryPage.tsx
 * =======================
 * Private Evidence Library (0053-F4): metadata create/list only.
 * No file upload/download, verification, public sharing, or claim linker.
 */

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Info, Library } from "lucide-react";
import { evidenceApi, platformApi } from "../lib/api";
import type {
  ApiError,
  EvidenceCreateRequest,
  EvidenceKind,
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

const SAFE_CLAIM_NOTE =
  "Claim linking will be added after claim selection UI is available.";

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

  const listQuery = useQuery({
    queryKey: ["evidence", "list"],
    queryFn: () => evidenceApi.listEvidence(),
  });

  const subjectsQuery = useQuery({
    queryKey: ["platform", "subjects"],
    queryFn: () => platformApi.listPlatformSubjects(),
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
          Metadata only in this version. No file upload yet. Evidence is not
          independently verified. Linking evidence does not independently
          confirm a claim.
        </p>
      </header>

      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
            This library stores private evidence metadata that may later support
            career claims. In this version, CareerKundi does not upload files,
            confirm document authenticity, or make evidence public.
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
                hint="Optional reference string. This is not a file upload."
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
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: "0.75rem" }}>
                {listQuery.data.map((row) => (
                  <li key={row.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(row.id)}
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
                        {row.subject_id ? ` · subject ${shortId(row.subject_id)}` : ""}
                      </div>
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
                Select a record to view private metadata details.
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
                  Storage URI: {selected.storage_uri || "None (metadata only)"}
                </div>
                <div>MIME: {selected.mime_type || "—"}</div>
                <div>Size bytes: {selected.size_bytes ?? "—"}</div>
                <div>Hash: {selected.content_hash || "—"}</div>
                <div style={{ color: "var(--text-secondary)", marginTop: 4 }}>
                  {selected.truth_warning}
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  Created {formatDate(selected.created_at)}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card padding="lg" style={{ marginBottom: "1.25rem" }}>
        <CardHeader>
          <CardTitle>Claim linking</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ color: "var(--text-secondary)" }}>{SAFE_CLAIM_NOTE}</p>
        </CardContent>
      </Card>

      <Card padding="lg">
        <CardHeader>
          <CardTitle>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              <Archive size={18} aria-hidden />
              Future attachment storage
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
            File attachment storage is not enabled yet. F5 will decide the
            storage backend, retention, deletion, and safety checks before
            uploads are allowed.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
