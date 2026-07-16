/**
 * PassportEvidencePanel — 0053-F8 / F11 private evidence awareness + review request.
 *
 * Shows evidence-linked claim summaries and private review request/cancel.
 * Does not upload, download, link, verify, approve, reject, or share.
 * A review request is not verification.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { evidenceApi, reviewRequestApi } from "@/lib/api";
import type {
  ApiError,
  PassportEvidenceSummaryItem,
  ReviewRequestRead,
} from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Textarea } from "@/components/ui/Input";
import { Spinner } from "@/components/ui/Spinner";
import styles from "./PassportPage.module.css";

function activeRequestForClaim(
  requests: ReviewRequestRead[] | undefined,
  claimId: string,
): ReviewRequestRead | undefined {
  return requests?.find(
    (row) => row.claim_id === claimId && row.review_state === "requested",
  );
}

function latestCancelledForClaim(
  requests: ReviewRequestRead[] | undefined,
  claimId: string,
): ReviewRequestRead | undefined {
  const cancelled =
    requests?.filter(
      (row) => row.claim_id === claimId && row.review_state === "cancelled",
    ) ?? [];
  if (cancelled.length === 0) return undefined;
  return [...cancelled].sort((a, b) =>
    (b.updated_at || "").localeCompare(a.updated_at || ""),
  )[0];
}

function ClaimReviewControls({
  item,
  requests,
}: {
  item: PassportEvidenceSummaryItem;
  requests: ReviewRequestRead[] | undefined;
}) {
  const queryClient = useQueryClient();
  const [requestNote, setRequestNote] = useState("");
  const [cancelReason, setCancelReason] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const active = activeRequestForClaim(requests, item.claim_id);
  const cancelled = latestCancelledForClaim(requests, item.claim_id);

  const createMutation = useMutation({
    mutationFn: () =>
      reviewRequestApi.createReviewRequest({
        claim_id: item.claim_id,
        request_note: requestNote.trim() || null,
      }),
    onSuccess: async () => {
      setErrorMessage(null);
      setStatusMessage("Review requested. This is not verification.");
      setRequestNote("");
      await queryClient.invalidateQueries({ queryKey: ["review-requests"] });
    },
    onError: (err: unknown) => {
      setStatusMessage(null);
      const apiMessage = ((err as ApiError)?.message || "").toLowerCase();
      if (apiMessage.includes("linked private evidence")) {
        setErrorMessage("Link private evidence before requesting review.");
      } else {
        setErrorMessage(
          (err as ApiError)?.message ||
            "Could not request private review. Please try again.",
        );
      }
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () =>
      reviewRequestApi.cancelReviewRequest(active!.id, {
        cancellation_reason: cancelReason.trim() || null,
      }),
    onSuccess: async () => {
      setErrorMessage(null);
      setStatusMessage(
        "Review request cancelled. Claim remains not independently verified.",
      );
      setCancelReason("");
      await queryClient.invalidateQueries({ queryKey: ["review-requests"] });
    },
    onError: (err: unknown) => {
      setStatusMessage(null);
      setErrorMessage(
        (err as ApiError)?.message ||
          "Could not cancel review request. Please try again.",
      );
    },
  });

  if (!item.claim_id) {
    return (
      <p className={styles.targetMeta}>
        Private review is unavailable for this item.
      </p>
    );
  }

  return (
    <div className={styles.reviewControls}>
      <p className={styles.targetMeta}>
        Claim status: Not independently verified
      </p>
      <p className={styles.targetTruth}>
        Request intake requires linked private evidence. A request is not
        verification.
      </p>
      <p className={styles.targetMeta}>
        Linked evidence is required for intake, but file attachment safety
        review is not enabled yet.
      </p>

      {active && (
        <>
          <p className={styles.targetRole}>
            {active.review_state_label || "Review requested"}
          </p>
          <p className={styles.targetMeta}>{active.review_state_help_text}</p>
          <p className={styles.targetTruth}>{active.warning}</p>
          <Textarea
            label="Optional cancellation reason"
            rows={2}
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            fullWidth
          />
          <Button
            size="sm"
            variant="secondary"
            loading={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate()}
          >
            Cancel review request
          </Button>
        </>
      )}

      {!active && (
        <>
          {cancelled && (
            <p className={styles.targetMeta}>
              Previous review request: {cancelled.review_state_label}. Claim
              remains not independently verified.
            </p>
          )}
          <Textarea
            label="Optional note for future review"
            rows={2}
            value={requestNote}
            onChange={(e) => setRequestNote(e.target.value)}
            fullWidth
          />
          <Button
            size="sm"
            variant="secondary"
            loading={createMutation.isPending}
            onClick={() => createMutation.mutate()}
          >
            Request private review
          </Button>
        </>
      )}

      {statusMessage && (
        <p className={styles.successBanner} role="status">
          {statusMessage}
        </p>
      )}
      {errorMessage && (
        <p className={styles.errorMessage} role="alert">
          {errorMessage}
        </p>
      )}
    </div>
  );
}

export default function PassportEvidencePanel() {
  const summaryQuery = useQuery({
    queryKey: ["evidence", "passport-summary"],
    queryFn: () => evidenceApi.getEvidencePassportSummary(),
    retry: false,
  });

  const reviewQuery = useQuery({
    queryKey: ["review-requests"],
    queryFn: () => reviewRequestApi.listReviewRequests(),
    retry: false,
  });

  const summary = summaryQuery.data;
  const requests = reviewQuery.data;

  return (
    <section
      className={styles.evidenceAwareness}
      aria-labelledby="passport-evidence-awareness"
    >
      <Card>
        <CardHeader>
          <CardTitle className={styles.privacyTitle}>
            <FileText size={18} aria-hidden="true" />
            <span id="passport-evidence-awareness">
              Private evidence awareness
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className={styles.evidenceBody}>
          <p className={styles.emptyBody}>
            Evidence linked here is private and not independently verified.
            Linking evidence does not verify your Passport, your profile, or a
            claim.
          </p>
          <p className={styles.emptyBody}>
            Requesting a review does not verify a claim. Review outcomes require
            a future explicit review workflow.
          </p>

          {summaryQuery.isLoading && (
            <div className={styles.evidenceLoading} aria-busy="true">
              <Spinner size="sm" label="Loading evidence links" />
              <p className={styles.stateHint}>Loading evidence links…</p>
            </div>
          )}

          {summaryQuery.isError && (
            <p className={styles.errorMessage} role="alert">
              {(summaryQuery.error as unknown as ApiError)?.message ||
                "Could not load private evidence awareness."}
            </p>
          )}

          {summaryQuery.isSuccess && summary && summary.items.length === 0 && (
            <div className={styles.evidenceEmpty}>
              <p className={styles.emptyBody}>
                No evidence-linked claims yet. Manage evidence in the Evidence
                Library.
              </p>
              <Link to="/evidence">
                <Button size="sm" variant="secondary">
                  Open Evidence Library
                </Button>
              </Link>
            </div>
          )}

          {summaryQuery.isSuccess && summary && summary.items.length > 0 && (
            <>
              <p className={styles.sectionCount}>
                {summary.linked_claims_count}{" "}
                {summary.linked_claims_count === 1
                  ? "claim with linked evidence"
                  : "claims with linked evidence"}{" "}
                · {summary.evidence_records_count}{" "}
                {summary.evidence_records_count === 1
                  ? "evidence record"
                  : "evidence records"}
              </p>
              {reviewQuery.isLoading && (
                <p className={styles.stateHint}>Loading review requests…</p>
              )}
              <ul className={styles.evidenceList}>
                {summary.items.map((item) => (
                  <li
                    key={`${item.claim_id}-${item.evidence_id}-${item.link_role}`}
                    className={styles.evidenceItem}
                  >
                    <p className={styles.targetRole}>{item.claim_value}</p>
                    <p className={styles.targetMeta}>
                      Claim kind: {item.claim_kind} · Link role:{" "}
                      {item.link_role_label || item.link_role}
                    </p>
                    <p className={styles.targetMeta}>
                      Evidence: {item.evidence_title} (
                      {item.evidence_kind_label || item.evidence_kind})
                    </p>
                    <p className={styles.targetMeta}>
                      Attachment:{" "}
                      {item.has_attachment
                        ? "Private file attached — scan not available"
                        : "No file attached"}
                    </p>
                    {item.has_attachment && (
                      <p className={styles.targetTruth}>
                        {item.attachment_safety_warning ||
                          "Attached files are not malware-scanned or reviewed in this version."}
                      </p>
                    )}
                    <div className={styles.evidenceBadges}>
                      <Badge color="default" size="sm">
                        {item.claim_support_label}
                      </Badge>
                      <Badge color="amber" size="sm">
                        Not independently verified
                      </Badge>
                    </div>
                    <p className={styles.targetTruth}>{item.truth_warning}</p>
                    <ClaimReviewControls item={item} requests={requests} />
                  </li>
                ))}
              </ul>
              <Link to="/evidence">
                <Button size="sm" variant="secondary">
                  Open Evidence Library
                </Button>
              </Link>
            </>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
