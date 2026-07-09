import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildSavedJobSearchPageParams,
  buildSavedJobSearchQueryKey,
  hasActiveSavedJobSearchFilter,
  type SavedJobSearchFilters,
} from "./savedJobSearchFilters";


const PAGE_SIZE = 20;


describe("structured saved-job search contract", () => {
  it("activates and aligns a location-only search", () => {
    const filters: SavedJobSearchFilters = {
      q: "",
      location: "  London  ",
      employmentType: "",
      remote: undefined,
    };

    expect(
      hasActiveSavedJobSearchFilter(
        filters,
      ),
    ).toBe(true);

    const params = buildSavedJobSearchPageParams(
      filters,
      1,
      PAGE_SIZE,
    );

    const key = buildSavedJobSearchQueryKey(
      filters,
      1,
      PAGE_SIZE,
    );

    expect(params).toEqual({
      q: undefined,
      location: "London",
      employment_type: undefined,
      remote: undefined,
      page: 1,
      page_size: 20,
    });

    expect(key[1]).toEqual({
      q: params.q,
      location: params.location,
      employment_type: params.employment_type,
      remote: params.remote,
    });
  });

  it("activates and preserves an employment-only exact value", () => {
    const filters: SavedJobSearchFilters = {
      q: "",
      location: "",
      employmentType: " Full-time ",
      remote: undefined,
    };

    expect(
      hasActiveSavedJobSearchFilter(
        filters,
      ),
    ).toBe(true);

    expect(
      buildSavedJobSearchPageParams(
        filters,
        2,
        PAGE_SIZE,
      ),
    ).toEqual({
      q: undefined,
      location: undefined,
      employment_type: " Full-time ",
      remote: undefined,
      page: 2,
      page_size: 20,
    });
  });

  it("activates and aligns a remote-only search", () => {
    const filters: SavedJobSearchFilters = {
      q: "",
      location: "",
      employmentType: "",
      remote: true,
    };

    expect(
      hasActiveSavedJobSearchFilter(
        filters,
      ),
    ).toBe(true);

    const params = buildSavedJobSearchPageParams(
      filters,
      3,
      PAGE_SIZE,
    );

    const key = buildSavedJobSearchQueryKey(
      filters,
      3,
      PAGE_SIZE,
    );

    expect(params.remote).toBe(true);
    expect(key[1].remote).toBe(true);
    expect(key[2]).toBe(3);
    expect(key[3]).toBe(20);
  });

  it("returns to an inactive contract when all visible filters are cleared", () => {
    const filters: SavedJobSearchFilters = {
      q: "",
      location: "",
      employmentType: "",
      remote: undefined,
    };

    expect(
      hasActiveSavedJobSearchFilter(
        filters,
      ),
    ).toBe(false);

    expect(
      buildSavedJobSearchPageParams(
        filters,
        1,
        PAGE_SIZE,
      ),
    ).toEqual({
      q: undefined,
      location: undefined,
      employment_type: undefined,
      remote: undefined,
      page: 1,
      page_size: 20,
    });
  });
});
