import { describe, expect, it, vi } from "vitest";

import {
  invalidateSavedJobQueries,
} from "./savedJobQueryInvalidation";


describe("invalidateSavedJobQueries", () => {
  it("invalidates the base saved-job and saved-search query families", async () => {
    const invalidateQueries = vi.fn()
      .mockResolvedValue(undefined);

    await invalidateSavedJobQueries({
      invalidateQueries,
    });

    expect(invalidateQueries).toHaveBeenCalledTimes(2);

    expect(invalidateQueries).toHaveBeenNthCalledWith(
      1,
      {
        queryKey: ["jobs"],
      },
    );

    expect(invalidateQueries).toHaveBeenNthCalledWith(
      2,
      {
        queryKey: ["jobs-search"],
      },
    );
  });

  it("awaits invalidation of both query families", async () => {
    let resolveJobs: (() => void) | undefined;
    let resolveSearch: (() => void) | undefined;

    const jobsInvalidation = new Promise<void>((resolve) => {
      resolveJobs = resolve;
    });

    const searchInvalidation = new Promise<void>((resolve) => {
      resolveSearch = resolve;
    });

    const invalidateQueries = vi.fn()
      .mockImplementation(
        ({ queryKey }: { queryKey: readonly unknown[] }) => (
          queryKey[0] === "jobs"
            ? jobsInvalidation
            : searchInvalidation
        ),
      );

    let completed = false;

    const pending = invalidateSavedJobQueries({
      invalidateQueries,
    }).then(() => {
      completed = true;
    });

    await Promise.resolve();

    expect(completed).toBe(false);

    resolveJobs?.();
    await Promise.resolve();

    expect(completed).toBe(false);

    resolveSearch?.();
    await pending;

    expect(completed).toBe(true);
  });
});
