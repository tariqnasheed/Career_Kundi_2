/**
 * PassportEvidencePanel — 0053-F8 read-only private evidence awareness.
 *
 * Shows evidence-linked claim summaries. Does not upload, download, link,
 * verify, or share. Linking evidence does not verify Passport/profile/claims.
 */

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { FileText } from "lucide-react";
import { evidenceApi } from "@/lib/api";
import type { ApiError } from "@/types/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import styles from "./PassportPage.module.css";

export default function PassportEvidencePanel() {
  const summaryQuery = useQuery({
    queryKey: ["evidence", "passport-summary"],
    queryFn: () => evidenceApi.getEvidencePassportSummary(),
    retry: false,
  });

  const summary = summaryQuery.data;

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
                        ? "Private file attached"
                        : "No file attached"}
                    </p>
                    <div className={styles.evidenceBadges}>
                      <Badge color="default" size="sm">
                        {item.claim_support_label}
                      </Badge>
                      <Badge color="amber" size="sm">
                        Not independently verified
                      </Badge>
                    </div>
                    <p className={styles.targetTruth}>{item.truth_warning}</p>
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
