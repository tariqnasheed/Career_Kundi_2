import { describe, expect, it } from "vitest";

import {
  resolveSavedJobSearchView,
} from "./savedJobSearchView";


describe("resolveSavedJobSearchView", () => {
  it("uses the full saved-job list when no filter is active", () => {
    const allJobs = ["job-a", "job-b"];

    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: false,
      allJobs,
      searchResults: undefined,
      searchPending: true,
      searchError: true,
    });

    expect(resolved).toEqual({
      jobs: allJobs,
      state: "unfiltered",
    });
  });

  it("does not fall back to allJobs while an active search is pending", () => {
    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: true,
      allJobs: ["local-job"],
      searchResults: undefined,
      searchPending: true,
      searchError: false,
    });

    expect(resolved).toEqual({
      jobs: [],
      state: "search_loading",
    });
  });

  it("represents an active search failure explicitly", () => {
    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: true,
      allJobs: ["local-job"],
      searchResults: ["stale-search-job"],
      searchPending: false,
      searchError: true,
    });

    expect(resolved).toEqual({
      jobs: [],
      state: "search_error",
    });
  });

  it("represents a defined empty backend result as no matches", () => {
    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: true,
      allJobs: ["local-job"],
      searchResults: [],
      searchPending: false,
      searchError: false,
    });

    expect(resolved).toEqual({
      jobs: [],
      state: "search_empty",
    });
  });

  it("uses backend search results when matches exist", () => {
    const searchResults = ["search-job-a", "search-job-b"];

    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: true,
      allJobs: ["local-job"],
      searchResults,
      searchPending: false,
      searchError: false,
    });

    expect(resolved).toEqual({
      jobs: searchResults,
      state: "search_results",
    });
  });

  it("treats unresolved active-search data as loading instead of local fallback", () => {
    const resolved = resolveSavedJobSearchView({
      hasActiveFilter: true,
      allJobs: ["local-job"],
      searchResults: undefined,
      searchPending: false,
      searchError: false,
    });

    expect(resolved).toEqual({
      jobs: [],
      state: "search_loading",
    });
  });
});
