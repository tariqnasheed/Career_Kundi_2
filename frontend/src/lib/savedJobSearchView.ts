export type SavedJobSearchViewState =
  | "unfiltered"
  | "search_loading"
  | "search_error"
  | "search_empty"
  | "search_results";


export interface SavedJobSearchView<T> {
  jobs: T[];
  state: SavedJobSearchViewState;
}


export interface ResolveSavedJobSearchViewInput<T> {
  hasActiveFilter: boolean;
  allJobs: T[] | undefined;
  searchResults: T[] | undefined;
  searchPending: boolean;
  searchError: boolean;
}


export function resolveSavedJobSearchView<T>(
  input: ResolveSavedJobSearchViewInput<T>,
): SavedJobSearchView<T> {
  if (!input.hasActiveFilter) {
    return {
      jobs: input.allJobs ?? [],
      state: "unfiltered",
    };
  }

  if (input.searchError) {
    return {
      jobs: [],
      state: "search_error",
    };
  }

  if (input.searchPending) {
    return {
      jobs: [],
      state: "search_loading",
    };
  }

  if (input.searchResults === undefined) {
    return {
      jobs: [],
      state: "search_loading",
    };
  }

  if (input.searchResults.length === 0) {
    return {
      jobs: [],
      state: "search_empty",
    };
  }

  return {
    jobs: input.searchResults,
    state: "search_results",
  };
}
