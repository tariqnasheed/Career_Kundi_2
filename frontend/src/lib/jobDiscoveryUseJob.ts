import type {
  JobDiscoveryResult,
  SavedJobRead,
} from "../types/api";

export type DiscoveryUseOutcome =
  | "parsed"
  | "preview_saved"
  | "mock_saved";

export interface DiscoveryUseResult {
  job: SavedJobRead;
  outcome: DiscoveryUseOutcome;
}

export interface DiscoveryUseDependencies {
  parse: (payload: {
    url?: string;
    pasted_text?: string;
  }) => Promise<SavedJobRead>;
  save: (
    payload: Record<string, unknown>,
  ) => Promise<SavedJobRead>;
}

export interface DiscoveryResultsNotice {
  kind: "mock" | "unverified";
  message: string;
}

function sourceHostname(sourceUrl: string): string {
  try {
    return new URL(sourceUrl).hostname.toLowerCase();
  } catch {
    return "";
  }
}

export function isMockDiscoveryHit(
  hit: JobDiscoveryResult,
): boolean {
  const hostname = sourceHostname(hit.source_url);
  const isExampleHost =
    hostname === "example.com"
    || hostname.endsWith(".example.com");

  const hasMockMarker = (hit.snippet ?? "")
    .toLowerCase()
    .includes("mock listing");

  return isExampleHost || hasMockMarker;
}

function previewSavePayload(
  hit: JobDiscoveryResult,
): Record<string, unknown> {
  return {
    title: hit.title,
    company_name: hit.company_name,
    location: hit.location,
    employment_type: hit.employment_type,
    is_remote: hit.is_remote,
    description_raw: hit.snippet,
    source_url: hit.source_url,
    source_site: hit.source_site,
    import_method: "search",
  };
}

export async function useDiscoveryHit(
  hit: JobDiscoveryResult,
  dependencies: DiscoveryUseDependencies,
): Promise<DiscoveryUseResult> {
  if (isMockDiscoveryHit(hit)) {
    const job = await dependencies.save(
      previewSavePayload(hit),
    );

    return {
      job,
      outcome: "mock_saved",
    };
  }

  if (hit.source_url) {
    try {
      const job = await dependencies.parse({
        url: hit.source_url,
      });

      return {
        job,
        outcome: "parsed",
      };
    } catch {
      const job = await dependencies.save(
        previewSavePayload(hit),
      );

      return {
        job,
        outcome: "preview_saved",
      };
    }
  }

  const job = await dependencies.save(
    previewSavePayload(hit),
  );

  return {
    job,
    outcome: "preview_saved",
  };
}

export function getDiscoveryResultsNotice(
  hits: JobDiscoveryResult[],
): DiscoveryResultsNotice | null {
  if (hits.length === 0) {
    return null;
  }

  const mockCount = hits.filter(
    isMockDiscoveryHit,
  ).length;

  if (mockCount === hits.length) {
    return {
      kind: "mock",
      message: (
        "Mock preview results only — configure "
        + "SERPAPI_KEY for live web search."
      ),
    };
  }

  if (hits.some((hit) => !hit.verified)) {
    return {
      kind: "unverified",
      message: (
        "Some results are unverified previews — "
        + "full details are checked when you use a job."
      ),
    };
  }

  return null;
}
