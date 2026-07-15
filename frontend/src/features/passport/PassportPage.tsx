/**
 * features/passport/PassportPage.tsx
 * ==================================
 * Career & Education Passport overview + full section editing (0052-F5/F6).
 */

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Briefcase,
  GraduationCap,
  FolderKanban,
  Wrench,
  Award,
  Target,
  UserRound,
  Shield,
  RefreshCw,
} from "lucide-react";
import { passportApi } from "@/lib/api";
import type {
  ApiError,
  PassportRead,
  PassportSectionKey,
  PassportSectionPreference,
} from "@/types/api";
import { useUIStore } from "@/store/ui";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import {
  PASSPORT_CONFLICT_MESSAGE,
  PassportCredentialEditor,
  PassportEducationEditor,
  PassportExperienceEditor,
  PassportProfileEditor,
  PassportProjectEditor,
  PassportSkillEditor,
  PassportTargetEditor,
} from "./PassportEditForms";
import styles from "./PassportPage.module.css";

const SECTION_META: Record<
  PassportSectionKey,
  { title: string; description: string; icon: React.ReactNode }
> = {
  profile: {
    title: "Profile",
    description: "Personal and professional identity details.",
    icon: <UserRound size={18} aria-hidden="true" />,
  },
  experience: {
    title: "Experience",
    description: "Roles and work history from your profile.",
    icon: <Briefcase size={18} aria-hidden="true" />,
  },
  education: {
    title: "Education",
    description: "Degrees, institutions and study history.",
    icon: <GraduationCap size={18} aria-hidden="true" />,
  },
  projects: {
    title: "Projects",
    description: "Portfolio and project highlights.",
    icon: <FolderKanban size={18} aria-hidden="true" />,
  },
  skills: {
    title: "Skills",
    description: "Technical and professional skills.",
    icon: <Wrench size={18} aria-hidden="true" />,
  },
  credentials: {
    title: "Credentials",
    description: "Certifications and credential references.",
    icon: <Award size={18} aria-hidden="true" />,
  },
  targets: {
    title: "Career targets",
    description: "Roles and pathways you are working toward.",
    icon: <Target size={18} aria-hidden="true" />,
  },
};

const EDITABLE_SECTIONS = new Set<PassportSectionKey>([
  "profile",
  "experience",
  "education",
  "projects",
  "skills",
  "credentials",
  "targets",
]);

function formatDate(value: string | null | undefined): string {
  if (!value) return "Not set";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Date unavailable";
  try {
    return parsed.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "Date unavailable";
  }
}

function formatMetaLabel(value: string | null | undefined): string {
  switch (value) {
    case "profile_supported":
      return "Profile-backed";
    case "not_provided":
      return "Self-declared";
    case "unverified":
      return "Unverified";
    case "user_asserted":
      return "Added by you";
    case "suggested_accepted":
      return "Accepted suggestion";
    default:
      return "Status unavailable";
  }
}

function sectionCount(passport: PassportRead, key: PassportSectionKey): number {
  switch (key) {
    case "profile":
      return passport.profile?.professional_headline || passport.profile?.bio_summary
        ? 1
        : 0;
    case "experience":
      return passport.experiences.length;
    case "education":
      return passport.education.length;
    case "projects":
      return passport.projects.length;
    case "skills":
      return passport.skills.length;
    case "credentials":
      return passport.credentials.length;
    case "targets":
      return passport.targets.length;
    default:
      return 0;
  }
}

function orderedPreferences(
  prefs: PassportSectionPreference[],
): PassportSectionPreference[] {
  return [...prefs].sort((a, b) => a.order_index - b.order_index);
}

function isEmptyPassport(passport: PassportRead): boolean {
  return (
    !passport.headline &&
    !passport.summary &&
    passport.experiences.length === 0 &&
    passport.education.length === 0 &&
    passport.projects.length === 0 &&
    passport.skills.length === 0 &&
    passport.credentials.length === 0 &&
    passport.targets.length === 0
  );
}

export default function PassportPage() {
  const queryClient = useQueryClient();
  const addToast = useUIStore((s) => s.addToast);
  const [banner, setBanner] = useState<{
    type: "success" | "warning";
    message: string;
  } | null>(null);

  const passportQuery = useQuery({
    queryKey: ["passport", "aggregate"],
    queryFn: () => passportApi.get(),
    retry: false,
  });

  const passport = passportQuery.data;
  const orderedSections = useMemo(
    () => (passport ? orderedPreferences(passport.section_preferences) : []),
    [passport],
  );

  const handleSaved = (next: PassportRead) => {
    queryClient.setQueryData(["passport", "aggregate"], next);
    setBanner({ type: "success", message: "Passport updated." });
    addToast({ type: "success", message: "Passport updated." });
  };

  const handleConflict = () => {
    setBanner({ type: "warning", message: PASSPORT_CONFLICT_MESSAGE });
    addToast({ type: "warning", message: PASSPORT_CONFLICT_MESSAGE });
    void passportQuery.refetch();
  };

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <p className={styles.eyebrow}>Career Core</p>
        <h1 className={styles.title}>Career &amp; Education Passport</h1>
        <p className={styles.lead}>
          A private, structured view of your career and education history.
        </p>
      </header>

      {passportQuery.isLoading && (
        <div className={styles.stateBlock} aria-busy="true">
          <Spinner size="lg" label="Loading your Career Passport" />
          <p className={styles.stateHint}>Loading your private Passport…</p>
        </div>
      )}

      {passportQuery.isError && (
        <Card className={styles.stateCard} role="alert">
          <CardContent className={styles.errorContent}>
            <p className={styles.errorTitle}>Could not load your Passport</p>
            <p className={styles.errorMessage}>
              {(passportQuery.error as unknown as ApiError)?.message ||
                "Something went wrong while loading your Passport. Please try again."}
            </p>
            <Button
              size="sm"
              leftIcon={<RefreshCw size={14} aria-hidden="true" />}
              onClick={() => void passportQuery.refetch()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      )}

      {passportQuery.isSuccess && passport && (
        <>
          <section className={styles.statusStrip} aria-label="Passport status">
            <Badge color="violet" size="sm" title="Private — visible only to you.">
              Private
            </Badge>
            <Badge
              color="amber"
              size="sm"
              title="Unverified — information has not been independently verified."
            >
              Unverified
            </Badge>
            <span className={styles.statusMeta}>Version {passport.version}</span>
            <span className={styles.statusMeta}>
              Updated {formatDate(passport.updated_at)}
            </span>
          </section>
          <p className={styles.statusExplain}>
            Private — visible only to you. Unverified — information has not been
            independently verified.
          </p>

          {banner && (
            <p
              className={
                banner.type === "success" ? styles.successBanner : styles.warningBanner
              }
              role="status"
            >
              {banner.message}
            </p>
          )}

          <section className={styles.identity} aria-labelledby="passport-identity">
            <h2 id="passport-identity" className={styles.sectionHeading}>
              Identity
            </h2>
            <Card>
              <CardContent className={styles.identityBody}>
                <p className={styles.displayName}>
                  {passport.display_name?.trim() || "Your Passport profile"}
                </p>
                <p className={styles.headline}>
                  {passport.headline?.trim() || "No professional headline yet"}
                </p>
                <p className={styles.summary}>
                  {passport.summary?.trim() || "No summary added yet"}
                </p>
              </CardContent>
            </Card>
          </section>

          <section className={styles.metrics} aria-label="Passport overview counts">
            {(
              [
                ["Experience", passport.experiences.length],
                ["Education", passport.education.length],
                ["Projects", passport.projects.length],
                ["Skills", passport.skills.length],
                ["Credentials", passport.credentials.length],
                ["Career targets", passport.targets.length],
              ] as const
            ).map(([label, count]) => (
              <div key={label} className={styles.metricCard}>
                <span className={styles.metricValue}>{count}</span>
                <span className={styles.metricLabel}>{label}</span>
              </div>
            ))}
          </section>

          {isEmptyPassport(passport) && (
            <Card className={styles.emptyCard}>
              <CardContent>
                <p className={styles.emptyLead}>
                  Your private Career Passport is ready.
                </p>
                <p className={styles.emptyBody}>
                  It will bring together your profile, experience, education,
                  projects, skills, credentials and career targets.
                </p>
                <p className={styles.emptyBody}>
                  You can edit every Passport section below. Your Passport stays
                  private and unverified until a later product step.
                </p>
              </CardContent>
            </Card>
          )}

          <section className={styles.sections} aria-labelledby="passport-sections">
            <h2 id="passport-sections" className={styles.sectionHeading}>
              Sections
            </h2>
            <div className={styles.sectionGrid}>
              {orderedSections.map((pref) => {
                const meta = SECTION_META[pref.section];
                const count = sectionCount(passport, pref.section);
                const editable = EDITABLE_SECTIONS.has(pref.section);
                return (
                  <Card key={pref.section} className={styles.sectionCard}>
                    <CardHeader className={styles.sectionCardHeader}>
                      <CardTitle className={styles.sectionCardTitle}>
                        <span className={styles.sectionIcon}>{meta.icon}</span>
                        {meta.title}
                      </CardTitle>
                      {!pref.enabled && (
                        <Badge color="default" size="sm">
                          Hidden in Passport view
                        </Badge>
                      )}
                    </CardHeader>
                    <CardContent className={styles.sectionBody}>
                      <p className={styles.sectionDescription}>{meta.description}</p>
                      <p className={styles.sectionCount}>
                        {pref.section === "profile"
                          ? count > 0
                            ? "Profile details present"
                            : "No profile details yet"
                          : `${count} ${count === 1 ? "entry" : "entries"}`}
                      </p>

                      {pref.section === "profile" && (
                        <PassportProfileEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "experience" && (
                        <PassportExperienceEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "education" && (
                        <PassportEducationEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "projects" && (
                        <PassportProjectEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "skills" && (
                        <PassportSkillEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "credentials" && (
                        <PassportCredentialEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}
                      {pref.section === "targets" && (
                        <PassportTargetEditor
                          passport={passport}
                          onSaved={handleSaved}
                          onConflict={handleConflict}
                        />
                      )}

                      {!editable && (
                        <p className={styles.readOnlyNote}>
                          Editing arrives in a later Passport step
                        </p>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </section>

          <section className={styles.targets} aria-labelledby="passport-targets">
            <h2 id="passport-targets" className={styles.sectionHeading}>
              Career targets
            </h2>
            {passport.targets.length === 0 ? (
              <p className={styles.emptyBody}>
                No career targets yet. Add a career target in the Targets section
                below. This is not a Roadmap yet.
              </p>
            ) : (
              <div className={styles.targetList}>
                {[...passport.targets]
                  .sort((a, b) => a.order_index - b.order_index)
                  .slice(0, 3)
                  .map((target) => (
                    <Card key={target.id}>
                      <CardContent className={styles.targetBody}>
                        <p className={styles.targetRole}>{target.target_role_text}</p>
                        <p className={styles.targetMeta}>
                          {[
                            target.target_country,
                            target.target_region,
                            target.target_seniority,
                            target.time_horizon,
                          ]
                            .filter(Boolean)
                            .join(" · ") || "Details not set yet"}
                        </p>
                        <p className={styles.targetPriority}>
                          Priority {target.priority}
                        </p>
                        <p className={styles.targetTruth}>
                          Career target · Not a Roadmap yet
                        </p>
                        {target.role_taxonomy?.taxonomy_id && (
                          <p className={styles.taxonomyHint}>
                            Suggested role match:{" "}
                            {target.role_taxonomy.normalized_text ||
                              target.role_taxonomy.input_text}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
              </div>
            )}
          </section>

          <section className={styles.privacy} aria-labelledby="passport-privacy">
            <Card>
              <CardHeader>
                <CardTitle className={styles.privacyTitle}>
                  <Shield size={18} aria-hidden="true" />
                  <span id="passport-privacy">Privacy and provenance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className={styles.emptyBody}>
                  Your Passport is private by default.
                </p>
                <p className={styles.emptyBody}>
                  Profile-backed means the information is stored in your
                  CareerKundi profile. It does not mean the information has been
                  independently verified.
                </p>
                <p className={styles.metaSample}>
                  Typical labels: {formatMetaLabel("profile_supported")},{" "}
                  {formatMetaLabel("unverified")}, {formatMetaLabel("user_asserted")}.
                </p>
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
