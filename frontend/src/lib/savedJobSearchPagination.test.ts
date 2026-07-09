import {
  describe,
  expect,
  it,
} from "vitest";

import {
  nextSavedJobSearchPage,
  previousSavedJobSearchPage,
  resolveSavedJobSearchPagination,
  shouldShowSavedJobSearchPagination,
  SAVED_JOB_SEARCH_PAGE_SIZE,
} from "./savedJobSearchPagination";


describe("saved-job search pagination", () => {
  it("uses the fixed B4.3C2 page size", () => {
    expect(
      SAVED_JOB_SEARCH_PAGE_SIZE,
    ).toBe(20);
  });

  it("disables previous navigation on page one", () => {
    expect(
      resolveSavedJobSearchPagination(
        1,
        true,
      ),
    ).toEqual({
      page: 1,
      canGoPrevious: false,
      canGoNext: true,
      showControls: true,
    });
  });

  it("shows no controls for a single terminal first page", () => {
    expect(
      resolveSavedJobSearchPagination(
        1,
        false,
      ),
    ).toEqual({
      page: 1,
      canGoPrevious: false,
      canGoNext: false,
      showControls: false,
    });
  });

  it("keeps previous navigation on a terminal later page", () => {
    expect(
      resolveSavedJobSearchPagination(
        3,
        false,
      ),
    ).toEqual({
      page: 3,
      canGoPrevious: true,
      canGoNext: false,
      showControls: true,
    });
  });

  it("never decrements below page one", () => {
    expect(
      previousSavedJobSearchPage(1),
    ).toBe(1);

    expect(
      previousSavedJobSearchPage(3),
    ).toBe(2);
  });

  it("advances only when the backend reports has_next", () => {
    expect(
      nextSavedJobSearchPage(
        2,
        true,
      ),
    ).toBe(3);

    expect(
      nextSavedJobSearchPage(
        2,
        false,
      ),
    ).toBe(2);
  });

  it("normalizes non-integer and invalid-low page inputs", () => {
    expect(
      resolveSavedJobSearchPagination(
        2.9,
        false,
      ).page,
    ).toBe(2);

    expect(
      previousSavedJobSearchPage(0),
    ).toBe(1);
  });

  it("keeps a Previous escape visible on an empty later page", () => {
    const pagination = resolveSavedJobSearchPagination(
      2,
      false,
    );

    expect(
      shouldShowSavedJobSearchPagination(
        true,
        "search_empty",
        pagination,
      ),
    ).toBe(true);
  });

  it("keeps a Previous escape visible on a failed later page", () => {
    const pagination = resolveSavedJobSearchPagination(
      3,
      false,
    );

    expect(
      shouldShowSavedJobSearchPagination(
        true,
        "search_error",
        pagination,
      ),
    ).toBe(true);
  });

  it("does not show pagination for an empty first page", () => {
    const pagination = resolveSavedJobSearchPagination(
      1,
      false,
    );

    expect(
      shouldShowSavedJobSearchPagination(
        true,
        "search_empty",
        pagination,
      ),
    ).toBe(false);
  });

  it("does not show pagination while search is loading", () => {
    const pagination = resolveSavedJobSearchPagination(
      2,
      true,
    );

    expect(
      shouldShowSavedJobSearchPagination(
        true,
        "search_loading",
        pagination,
      ),
    ).toBe(false);
  });
});
