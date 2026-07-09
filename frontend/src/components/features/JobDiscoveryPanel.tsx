/**
 * Top-of-page job discovery — paste URL, natural-language web search, filters,
 * and result cards with "Use this job" / "Open posting".
 */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Filter,
  Link2,
  ExternalLink,
  Briefcase,
  MapPin,
  Building,
  Globe,
  Loader2,
  CheckCircle,
} from "lucide-react";

import { jobApi } from "../../lib/api";
import {
  getDiscoveryResultsNotice,
  useDiscoveryHit,
} from "../../lib/jobDiscoveryUseJob";
import { useUIStore } from "../../store/ui";
import type {
  JobDiscoveryResult,
  SavedJobRead,
} from "../../types/api";

import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

interface JobDiscoveryPanelProps {
  onUseJob: (job: SavedJobRead) => void;
  usingUrl?: string | null;
}

export function JobDiscoveryPanel({
  onUseJob,
  usingUrl,
}: JobDiscoveryPanelProps) {
  const { addToast } = useUIStore();

  const [pasteUrl, setPasteUrl] = useState("");
  const [q, setQ] = useState("");
  const [location, setLocation] = useState("");
  const [employmentType, setEmploymentType] = useState("");
  const [remote, setRemote] = useState<
    boolean | undefined
  >(undefined);
  const [experienceLevel, setExperienceLevel] =
    useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [results, setResults] = useState<
    JobDiscoveryResult[]
  >([]);

  const discoverMutation = useMutation({
    mutationFn: (
      params: Parameters<typeof jobApi.discover>[0],
    ) => jobApi.discover(params),
    onSuccess: (hits) => {
      setResults(hits);

      if (!hits.length) {
        addToast({
          type: "info",
          message: (
            "No jobs found. Try different keywords "
            + "or paste a URL."
          ),
        });
      }
    },
    onError: () => {
      addToast({
        type: "error",
        message: (
          "Live job search failed. "
          + "Try again or paste a URL directly."
        ),
      });
    },
  });

  const useJobMutation = useMutation({
    mutationFn: (hit: JobDiscoveryResult) => (
      useDiscoveryHit(
        hit,
        {
          parse: jobApi.parse,
          save: jobApi.save,
        },
      )
    ),
    onSuccess: ({ job, outcome }) => {
      onUseJob(job);

      if (outcome === "parsed") {
        addToast({
          type: "success",
          message: (
            "Full job details extracted and loaded — "
            + "ready for interview pack and CV generation."
          ),
        });
        return;
      }

      if (outcome === "mock_saved") {
        addToast({
          type: "warning",
          message: (
            "Saved a mock preview only. "
            + "Configure SERPAPI_KEY for live discovery "
            + "before relying on this job data."
          ),
        });
        return;
      }

      addToast({
        type: "warning",
        message: (
          "Full job extraction failed. "
          + "Saved preview details only — "
          + "review the posting before generating materials."
        ),
      });
    },
    onError: () => {
      addToast({
        type: "error",
        message: (
          "Could not load or save this job. "
          + "Try opening the posting manually."
        ),
      });
    },
  });

  const runDiscover = (urlOverride?: string) => {
    const url = (
      urlOverride
      ?? (pasteUrl.trim() || undefined)
    );

    if (url) {
      discoverMutation.mutate({
        url,
      });
      return;
    }

    discoverMutation.mutate({
      q: q || undefined,
      location: location || undefined,
      employment_type: employmentType || undefined,
      remote,
      experience_level: experienceLevel || undefined,
    });
  };

  const resultsNotice = getDiscoveryResultsNotice(
    results,
  );

  return (
    <div
      className="feature-glass feature-panel"
      style={{
        marginBottom: "1.5rem",
      }}
    >
      <h2
        style={{
          fontFamily: "var(--font-heading)",
          fontWeight: 700,
          fontSize: "1.15rem",
          marginBottom: "0.35rem",
        }}
      >
        Find jobs on the web
      </h2>

      <p
        style={{
          fontSize: "0.8rem",
          color: "var(--text-secondary)",
          marginBottom: "1.25rem",
        }}
      >
        Paste a job URL or search live postings — then
        use a result to auto-fill interview prep and CV
        generation.
      </p>

      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <Input
          type="url"
          placeholder={(
            "Paste job URL "
            + "(LinkedIn, Indeed, company careers page…)"
          )}
          value={pasteUrl}
          onChange={(event) => {
            setPasteUrl(event.target.value);
          }}
          leftIcon={<Link2 size={15} />}
          fullWidth
          onKeyDown={(event) => {
            if (
              event.key === "Enter"
              && pasteUrl.trim()
            ) {
              runDiscover(pasteUrl.trim());
            }
          }}
        />

        <Button
          variant="primary"
          onClick={() => runDiscover()}
          loading={discoverMutation.isPending}
          disabled={!pasteUrl.trim() && !q.trim()}
        >
          {pasteUrl.trim() ? "Fetch" : "Search"}
        </Button>
      </div>

      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          marginBottom: showFilters ? "1rem" : 0,
        }}
      >
        <div
          style={{
            flex: 1,
          }}
        >
          <Input
            placeholder={(
              "e.g. remote Python backend roles "
              + "in London paying over £80k"
            )}
            value={q}
            onChange={(event) => {
              setQ(event.target.value);
            }}
            leftIcon={<Search size={15} />}
            fullWidth
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                runDiscover();
              }
            }}
          />
        </div>

        <Button
          variant="secondary"
          onClick={() => {
            setShowFilters(!showFilters);
          }}
          leftIcon={<Filter size={14} />}
        >
          Filters
        </Button>

        <Button
          variant="secondary"
          onClick={() => runDiscover()}
          loading={(
            discoverMutation.isPending
            && !pasteUrl.trim()
          )}
        >
          Search web
        </Button>
      </div>

      {showFilters && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: (
              "repeat(auto-fit, minmax(160px, 1fr))"
            ),
            gap: "0.75rem",
            paddingTop: "0.75rem",
            marginBottom: "1rem",
          }}
        >
          <Input
            label="Location"
            value={location}
            onChange={(event) => {
              setLocation(event.target.value);
            }}
            placeholder="London, Berlin, Remote"
            fullWidth
          />

          <Input
            label="Employment type"
            value={employmentType}
            onChange={(event) => {
              setEmploymentType(event.target.value);
            }}
            placeholder="Full-time, Contract"
            fullWidth
          />

          <div>
            <label
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                display: "block",
                marginBottom: "0.4rem",
              }}
            >
              Experience
            </label>

            <select
              value={experienceLevel}
              onChange={(event) => {
                setExperienceLevel(event.target.value);
              }}
              style={{
                width: "100%",
                padding: "0.55rem",
                borderRadius: "8px",
                background: "var(--bg-overlay)",
                border: "1px solid var(--border-subtle)",
                color: "var(--text-primary)",
                fontSize: "0.8rem",
              }}
            >
              <option value="">Any</option>
              <option value="entry">Entry</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </div>

          <div>
            <p
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                marginBottom: "0.4rem",
              }}
            >
              Work mode
            </p>

            <div
              style={{
                display: "flex",
                gap: "0.35rem",
              }}
            >
              {[
                {
                  label: "Any",
                  value: undefined,
                },
                {
                  label: "Remote",
                  value: true,
                },
                {
                  label: "On-site",
                  value: false,
                },
              ].map((option) => (
                <button
                  key={String(option.value)}
                  type="button"
                  onClick={() => {
                    setRemote(option.value);
                  }}
                  style={{
                    flex: 1,
                    padding: "0.35rem",
                    borderRadius: "8px",
                    fontSize: "0.72rem",
                    cursor: "pointer",
                    border: (
                      remote === option.value
                        ? "2px solid var(--accent-violet)"
                        : "1px solid var(--border-subtle)"
                    ),
                    background: (
                      remote === option.value
                        ? "rgba(139,92,246,0.08)"
                        : "transparent"
                    ),
                    color: (
                      remote === option.value
                        ? "var(--accent-violet)"
                        : "var(--text-secondary)"
                    ),
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {discoverMutation.isPending && (
        <div
          style={{
            textAlign: "center",
            padding: "2rem",
            color: "var(--text-secondary)",
          }}
        >
          <Loader2
            size={28}
            style={{
              animation: "spin 1s linear infinite",
              margin: "0 auto 0.75rem",
            }}
          />
          Searching live job postings…
        </div>
      )}

      <AnimatePresence>
        {!discoverMutation.isPending
          && results.length > 0 && (
          <motion.div
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.75rem",
              marginTop: "1rem",
            }}
          >
            <p
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
              }}
            >
              {results.length} result
              {results.length !== 1 ? "s" : ""}
              {resultsNotice
                ? ` — ${resultsNotice.message}`
                : " from the web"}
            </p>

            {results.map((hit, index) => (
              <motion.div
                key={`${hit.source_url}-${index}`}
                initial={{
                  opacity: 0,
                  y: 8,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay: index * 0.04,
                }}
                className={(
                  "feature-glass "
                  + "job-card-premium "
                  + "feature-glass--lift"
                )}
                style={{
                  gridTemplateColumns: "auto 1fr auto",
                  alignItems: "center",
                }}
              >
                <div className="job-card-premium__logo">
                  {(hit.company_name ?? "?")[0]
                    .toUpperCase()}
                </div>

                <div
                  style={{
                    minWidth: 0,
                  }}
                >
                  <p
                    style={{
                      fontWeight: 700,
                      fontFamily: "var(--font-heading)",
                      marginBottom: "0.25rem",
                    }}
                  >
                    {hit.title}
                  </p>

                  <div
                    style={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: "0.75rem",
                      fontSize: "0.75rem",
                      color: "var(--text-secondary)",
                      marginBottom: "0.35rem",
                    }}
                  >
                    {hit.company_name && (
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                      >
                        <Building size={12} />
                        {hit.company_name}
                      </span>
                    )}

                    {hit.location && (
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                      >
                        <MapPin size={12} />
                        {hit.location}
                      </span>
                    )}

                    {hit.employment_type && (
                      <span
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 4,
                        }}
                      >
                        <Briefcase size={12} />
                        {hit.employment_type}
                      </span>
                    )}

                    {hit.salary_hint && (
                      <span>
                        {hit.salary_hint}
                      </span>
                    )}
                  </div>

                  {hit.snippet && (
                    <p
                      style={{
                        fontSize: "0.78rem",
                        color: "var(--text-secondary)",
                        lineHeight: 1.5,
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {hit.snippet}
                    </p>
                  )}

                  <div
                    style={{
                      display: "flex",
                      gap: "0.35rem",
                      marginTop: "0.5rem",
                      flexWrap: "wrap",
                    }}
                  >
                    {hit.source_site && (
                      <Badge
                        color="default"
                        size="sm"
                      >
                        <Globe size={10} />
                        {" "}
                        {hit.source_site}
                      </Badge>
                    )}

                    {hit.is_remote && (
                      <Badge
                        color="emerald"
                        size="sm"
                      >
                        Remote
                      </Badge>
                    )}

                    {hit.verified && (
                      <Badge
                        color="emerald"
                        size="sm"
                      >
                        Live
                      </Badge>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    alignItems: "stretch",
                    minWidth: 140,
                  }}
                >
                  <Button
                    variant="primary"
                    size="sm"
                    leftIcon={(
                      usingUrl === hit.source_url
                      && useJobMutation.isPending
                        ? <Loader2 size={14} />
                        : <CheckCircle size={14} />
                    )}
                    onClick={() => {
                      useJobMutation.mutate(hit);
                    }}
                    loading={(
                      usingUrl === hit.source_url
                      && useJobMutation.isPending
                    )}
                    disabled={useJobMutation.isPending}
                  >
                    Use this job
                  </Button>

                  <Button
                    variant="secondary"
                    size="sm"
                    leftIcon={<ExternalLink size={14} />}
                    onClick={() => {
                      window.open(
                        hit.source_url,
                        "_blank",
                        "noopener,noreferrer",
                      );
                    }}
                  >
                    Open posting
                  </Button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
