// @vitest-environment node
/**
 * Unit test for the typed API client surface (src/lib/api.ts).
 *
 * Runs in the `node` environment and mocks axios, so the test verifies the
 * client's method surface (the frontend↔backend contract) without loading the
 * real HTTP transport or a DOM. This exercises that api.ts imports and
 * constructs cleanly and exposes every method the app depends on.
 */
import { describe, it, expect, vi } from "vitest";

// Mock axios so importing the client doesn't pull in the real HTTP stack.
vi.mock("axios", () => {
  const instance = {
    interceptors: { request: { use: () => {} }, response: { use: () => {} } },
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  };
  return { default: { create: () => instance } };
});

import { authApi, jobApi, cvApi, roadmapApi, profileApi } from "../../src/lib/api";

describe("API client surface", () => {
  it("exposes the job-search endpoints used across the app", () => {
    expect(typeof jobApi.list).toBe("function");
    expect(typeof jobApi.search).toBe("function");
    expect(typeof jobApi.updateStatus).toBe("function");
    expect(typeof jobApi.save).toBe("function");
    expect(typeof jobApi.generateInterviewPack).toBe("function");
  });

  it("exposes CV export, auth, profile, and roadmap methods", () => {
    expect(typeof cvApi.downloadPdf).toBe("function");
    expect(typeof cvApi.generate).toBe("function");
    expect(typeof authApi.login).toBe("function");
    expect(typeof profileApi.get).toBe("function");
    expect(typeof roadmapApi.generate).toBe("function");
  });
});
