export const SAVED_JOB_SEARCH_PAGE_SIZE = 20;


export interface SavedJobSearchPaginationState {
  page: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
  showControls: boolean;
}


export function resolveSavedJobSearchPagination(
  page: number,
  hasNext: boolean,
): SavedJobSearchPaginationState {
  const normalizedPage = Math.max(
    1,
    Math.trunc(page),
  );

  return {
    page: normalizedPage,
    canGoPrevious: normalizedPage > 1,
    canGoNext: hasNext,
    showControls: (
      normalizedPage > 1
      || hasNext
    ),
  };
}


export function previousSavedJobSearchPage(
  page: number,
): number {
  return Math.max(
    1,
    Math.trunc(page) - 1,
  );
}


export function nextSavedJobSearchPage(
  page: number,
  hasNext: boolean,
): number {
  const normalizedPage = Math.max(
    1,
    Math.trunc(page),
  );

  return hasNext
    ? normalizedPage + 1
    : normalizedPage;
}

export type SavedJobSearchPaginationViewState =
  | "unfiltered"
  | "search_loading"
  | "search_error"
  | "search_empty"
  | "search_results";


export function shouldShowSavedJobSearchPagination(
  hasActiveFilter: boolean,
  viewState: SavedJobSearchPaginationViewState,
  pagination: SavedJobSearchPaginationState,
): boolean {
  if (!hasActiveFilter) {
    return false;
  }

  if (viewState === "search_results") {
    return pagination.showControls;
  }

  if (
    viewState === "search_empty"
    || viewState === "search_error"
  ) {
    return pagination.canGoPrevious;
  }

  return false;
}
