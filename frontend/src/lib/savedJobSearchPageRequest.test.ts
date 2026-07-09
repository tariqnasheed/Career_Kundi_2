import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildSavedJobSearchPageRequest,
} from "./savedJobSearchPageRequest";


describe("buildSavedJobSearchPageRequest", () => {
  it("targets the additive paginated saved-search endpoint", () => {
    const request = buildSavedJobSearchPageRequest({
      q: "Engineer",
      page: 2,
      page_size: 20,
    });

    expect(request.url).toBe(
      "/job-search/search/page",
    );

    expect(request.params).toEqual({
      q: "Engineer",
      page: 2,
      page_size: 20,
    });
  });

  it("preserves the complete structured search parameter set", () => {
    const request = buildSavedJobSearchPageRequest({
      q: "Platform Engineer",
      location: "London",
      employment_type: "Full-time",
      remote: false,
      page: 3,
      page_size: 50,
    });

    expect(request.params).toEqual({
      q: "Platform Engineer",
      location: "London",
      employment_type: "Full-time",
      remote: false,
      page: 3,
      page_size: 50,
    });
  });

  it("does not trim or otherwise normalize caller values", () => {
    const params = {
      q: "  Engineer  ",
      location: "  London  ",
      remote: false,
      page: 1,
      page_size: 100,
    };

    const request = buildSavedJobSearchPageRequest(
      params,
    );

    expect(request.params).not.toBe(
      params,
    );

    expect(request.params).toEqual({
      q: "  Engineer  ",
      location: "  London  ",
      remote: false,
      page: 1,
      page_size: 100,
    });

    params.q = "Changed";

    expect(request.params.q).toBe(
      "  Engineer  ",
    );
  });
});
