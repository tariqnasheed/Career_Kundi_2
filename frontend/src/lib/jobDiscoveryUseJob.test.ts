import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  JobDiscoveryResult,
  SavedJobRead,
} from "../types/api";

import {
  getDiscoveryResultsNotice,
  isMockDiscoveryHit,
  useDiscoveryHit,
} from "./jobDiscoveryUseJob";

const liveHit: JobDiscoveryResult = {
  title: "Python Backend Engineer",
  company_name: "Example Co",
  location: "London",
  employment_type: "Full-time",
  is_remote: false,
  snippet: "Build reliable backend services.",
  source_url: "https://jobs.example.org/python-backend",
  source_site: "Example",
  salary_hint: null,
  verified: true,
};

const savedJob = {
  id: "saved-job-1",
  title: "Python Backend Engineer",
} as SavedJobRead;

describe("useDiscoveryHit", () => {
  it("returns parsed when full parse succeeds", async () => {
    const parse = vi.fn().mockResolvedValue(savedJob);
    const save = vi.fn();

    const result = await useDiscoveryHit(
      liveHit,
      {
        parse,
        save,
      },
    );

    expect(result).toEqual({
      job: savedJob,
      outcome: "parsed",
    });

    expect(parse).toHaveBeenCalledTimes(1);
    expect(parse).toHaveBeenCalledWith({
      url: liveHit.source_url,
    });
    expect(save).not.toHaveBeenCalled();
  });

  it(
    "returns preview_saved when parse fails and preview save succeeds",
    async () => {
      const parse = vi
        .fn()
        .mockRejectedValue(new Error("scrape failed"));

      const save = vi
        .fn()
        .mockResolvedValue(savedJob);

      const result = await useDiscoveryHit(
        liveHit,
        {
          parse,
          save,
        },
      );

      expect(result).toEqual({
        job: savedJob,
        outcome: "preview_saved",
      });

      expect(parse).toHaveBeenCalledTimes(1);
      expect(save).toHaveBeenCalledTimes(1);
      expect(save).toHaveBeenCalledWith({
        title: liveHit.title,
        company_name: liveHit.company_name,
        location: liveHit.location,
        employment_type: liveHit.employment_type,
        is_remote: liveHit.is_remote,
        description_raw: liveHit.snippet,
        source_url: liveHit.source_url,
        source_site: liveHit.source_site,
        import_method: "search",
      });
    },
  );

  it(
    "saves mock preview directly without attempting parse",
    async () => {
      const mockHit: JobDiscoveryResult = {
        ...liveHit,
        source_url: (
          "https://careers.example.com/example/python-1"
        ),
        snippet: (
          "Example mock listing for offline development."
        ),
        verified: false,
      };

      const parse = vi.fn();
      const save = vi
        .fn()
        .mockResolvedValue(savedJob);

      const result = await useDiscoveryHit(
        mockHit,
        {
          parse,
          save,
        },
      );

      expect(result).toEqual({
        job: savedJob,
        outcome: "mock_saved",
      });

      expect(isMockDiscoveryHit(mockHit)).toBe(true);
      expect(parse).not.toHaveBeenCalled();
      expect(save).toHaveBeenCalledTimes(1);
    },
  );
});

describe("getDiscoveryResultsNotice", () => {
  it(
    "classifies an all-mock result set without relying on the first verified flag",
    () => {
      const hits: JobDiscoveryResult[] = [
        {
          ...liveHit,
          source_url: "https://careers.example.com/a/1",
          snippet: "mock listing one",
          verified: false,
        },
        {
          ...liveHit,
          source_url: "https://careers.example.com/b/2",
          snippet: "mock listing two",
          verified: false,
        },
      ];

      expect(
        getDiscoveryResultsNotice(hits),
      ).toEqual({
        kind: "mock",
        message: (
          "Mock preview results only — configure "
          + "SERPAPI_KEY for live web search."
        ),
      });
    },
  );

  it(
    "classifies mixed verified and unverified results as unverified previews",
    () => {
      const unverifiedPreview: JobDiscoveryResult = {
        ...liveHit,
        source_url: "https://jobs.example.org/unverified",
        verified: false,
      };

      expect(
        getDiscoveryResultsNotice([
          liveHit,
          unverifiedPreview,
        ]),
      ).toEqual({
        kind: "unverified",
        message: (
          "Some results are unverified previews — "
          + "full details are checked when you use a job."
        ),
      });
    },
  );

  it(
    "returns no notice when every result is verified",
    () => {
      expect(
        getDiscoveryResultsNotice([
          liveHit,
          {
            ...liveHit,
            source_url: "https://jobs.example.org/second",
          },
        ]),
      ).toBeNull();
    },
  );
});
