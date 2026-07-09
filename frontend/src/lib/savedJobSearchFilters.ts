import type {
  SavedJobSearchPageParams,
} from "./savedJobSearchPageRequest";


export interface SavedJobSearchFilters {
  q: string;
  location: string;
  employmentType: string;
  remote: boolean | undefined;
}


export interface CanonicalSavedJobSearchFilters {
  q?: string;
  location?: string;
  employment_type?: string;
  remote?: boolean;
}


export const EMPTY_SAVED_JOB_SEARCH_FILTERS: SavedJobSearchFilters = {
  q: "",
  location: "",
  employmentType: "",
  remote: undefined,
};


export function canonicalizeSavedJobSearchFilters(
  filters: SavedJobSearchFilters,
): CanonicalSavedJobSearchFilters {
  const q = filters.q.trim();
  const location = filters.location.trim();

  const employmentType = (
    filters.employmentType.trim()
      ? filters.employmentType
      : undefined
  );

  return {
    q: q || undefined,
    location: location || undefined,
    employment_type: employmentType,
    remote: filters.remote,
  };
}


export function hasActiveSavedJobSearchFilter(
  filters: SavedJobSearchFilters,
): boolean {
  const canonical = canonicalizeSavedJobSearchFilters(
    filters,
  );

  return (
    canonical.q !== undefined
    || canonical.location !== undefined
    || canonical.employment_type !== undefined
    || canonical.remote !== undefined
  );
}


export function buildSavedJobSearchQueryKey(
  filters: SavedJobSearchFilters,
  page: number,
  pageSize: number,
) {
  const canonical = canonicalizeSavedJobSearchFilters(
    filters,
  );

  return [
    "jobs-search",
    canonical,
    page,
    pageSize,
  ] as const;
}


export function buildSavedJobSearchPageParams(
  filters: SavedJobSearchFilters,
  page: number,
  pageSize: number,
): SavedJobSearchPageParams {
  const canonical = canonicalizeSavedJobSearchFilters(
    filters,
  );

  return {
    ...canonical,
    page,
    page_size: pageSize,
  };
}
