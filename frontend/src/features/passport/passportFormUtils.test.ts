/**
 * passportFormUtils.test.ts
 */

import { describe, it, expect } from "vitest";
import {
  emptyToNull,
  splitLines,
  joinLines,
  splitCommaList,
  joinCommaList,
  normalizeDateInput,
  validateDateOrder,
  isConflictError,
  getApiErrorMessage,
} from "./passportFormUtils";

describe("passportFormUtils", () => {
  it("emptyToNull trims and converts blanks", () => {
    expect(emptyToNull("  hello ")).toBe("hello");
    expect(emptyToNull("   ")).toBeNull();
    expect(emptyToNull("")).toBeNull();
  });

  it("normalizes multiline lists and removes duplicates", () => {
    expect(splitLines("Alpha\n\nbeta\nALPHA\n gamma ")).toEqual([
      "Alpha",
      "beta",
      "gamma",
    ]);
    expect(joinLines(["a", "b"])).toBe("a\nb");
    expect(joinLines(null)).toBe("");
  });

  it("normalizes comma lists and removes duplicates", () => {
    expect(splitCommaList("React, , typescript, REACT, Vite")).toEqual([
      "React",
      "typescript",
      "Vite",
    ]);
    expect(joinCommaList(["a", "b"])).toBe("a, b");
  });

  it("normalizeDateInput keeps YYYY-MM-DD", () => {
    expect(normalizeDateInput("2024-01-15T12:00:00Z")).toBe("2024-01-15");
    expect(normalizeDateInput("")).toBe("");
    expect(normalizeDateInput(null)).toBe("");
  });

  it("validateDateOrder handles current role and invalid ranges", () => {
    expect(validateDateOrder("2020-01-01", "2019-01-01", true)).toBeNull();
    expect(validateDateOrder("2020-01-01", null, false)).toBeNull();
    expect(validateDateOrder("2020-01-01", "2019-01-01", false)).toBe(
      "End date must be on or after the start date.",
    );
    expect(validateDateOrder("2020-01-01", "2021-01-01", false)).toBeNull();
  });

  it("detects CONFLICT errors and safe messages", () => {
    expect(isConflictError({ code: "CONFLICT", message: "x" })).toBe(true);
    expect(isConflictError({ code: "VALIDATION_ERROR" })).toBe(false);
    expect(isConflictError(null)).toBe(false);
    expect(
      getApiErrorMessage({ message: "Backend said no" }, "fallback"),
    ).toBe("Backend said no");
    expect(getApiErrorMessage({}, "fallback")).toBe("fallback");
  });
});
