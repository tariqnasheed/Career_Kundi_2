import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildSavedJobSearchPageParams,
  buildSavedJobSearchQueryKey,
  canonicalizeSavedJobSearchFilters,
  EMPTY_SAVED_JOB_SEARCH_FILTERS,
  hasActiveSavedJobSearchFilter,
} from "./savedJobSearchFilters";


describe("saved-job structured search filters", () => {
  it("treats blank text and undefined remote as inactive", () => {
    expect(
      hasActiveSavedJobSearchFilter({
        q: "   ",
        location: "\t",
        employmentType: "  ",
        remote: undefined,
      }),
    ).toBe(false);

    expect(
      hasActiveSavedJobSearchFilter(
        EMPTY_SAVED_JOB_SEARCH_FILTERS,
      ),
    ).toBe(false);
  });

  it("treats remote false as an active filter", () => {
    expect(
      hasActiveSavedJobSearchFilter({
        ...EMPTY_SAVED_JOB_SEARCH_FILTERS,
        remote: false,
      }),
    ).toBe(true);
  });

  it("preserves remote false in canonical filters", () => {
    expect(
      canonicalizeSavedJobSearchFilters({
        ...EMPTY_SAVED_JOB_SEARCH_FILTERS,
        remote: false,
      }),
    ).toEqual({
      q: undefined,
      location: undefined,
      employment_type: undefined,
      remote: false,
    });
  });

  it("trims q and location but preserves exact nonblank employment type", () => {
    expect(
      canonicalizeSavedJobSearchFilters({
        q: "  Engineer  ",
        location: "  London  ",
        employmentType: " Full-time ",
        remote: undefined,
      }),
    ).toEqual({
      q: "Engineer",
      location: "London",
      employment_type: " Full-time ",
      remote: undefined,
    });
  });

  it("uses the same canonical filters for request params", () => {
    expect(
      buildSavedJobSearchPageParams(
        {
          q: "  Engineer ",
          location: " London ",
          employmentType: "Full-time",
          remote: false,
        },
        3,
        20,
      ),
    ).toEqual({
      q: "Engineer",
      location: "London",
      employment_type: "Full-time",
      remote: false,
      page: 3,
      page_size: 20,
    });
  });

  it("builds a query key with the saved-search prefix and page dimensions", () => {
    expect(
      buildSavedJobSearchQueryKey(
        {
          q: " Engineer ",
          location: "",
          employmentType: "",
          remote: true,
        },
        2,
        20,
      ),
    ).toEqual([
      "jobs-search",
      {
        q: "Engineer",
        location: undefined,
        employment_type: undefined,
        remote: true,
      },
      2,
      20,
    ]);
  });

  it("distinguishes undefined remote from remote false", () => {
    const anyRemoteKey = buildSavedJobSearchQueryKey(
      EMPTY_SAVED_JOB_SEARCH_FILTERS,
      1,
      20,
    );

    const falseRemoteKey = buildSavedJobSearchQueryKey(
      {
        ...EMPTY_SAVED_JOB_SEARCH_FILTERS,
        remote: false,
      },
      1,
      20,
    );

    expect(
      falseRemoteKey,
    ).not.toEqual(
      anyRemoteKey,
    );
  });

  it("keeps request params and query-key filters aligned", () => {
    const filters = {
      q: "  Platform Engineer  ",
      location: " London ",
      employmentType: "Contract",
      remote: false,
    };

    const params = buildSavedJobSearchPageParams(
      filters,
      4,
      20,
    );

    const key = buildSavedJobSearchQueryKey(
      filters,
      4,
      20,
    );

    expect(
      key[1],
    ).toEqual({
      q: params.q,
      location: params.location,
      employment_type: params.employment_type,
      remote: params.remote,
    });

    expect(key[2]).toBe(params.page);
    expect(key[3]).toBe(params.page_size);
  });
});
