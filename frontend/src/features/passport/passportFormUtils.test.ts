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
  clampPriority,
  normalizeSelectValue,
  buildUnknownRoleTaxonomy,
  buildUnknownSkillTaxonomy,
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

  it("clamps priority and builds unknown taxonomy refs", () => {
    expect(clampPriority(0)).toBe(1);
    expect(clampPriority(9)).toBe(5);
    expect(clampPriority("3")).toBe(3);
    expect(clampPriority("nope")).toBe(3);
    expect(normalizeSelectValue("  ")).toBeNull();
    expect(normalizeSelectValue(" mid ")).toBe("mid");
    expect(buildUnknownRoleTaxonomy("")).toBeNull();
    expect(buildUnknownRoleTaxonomy("  Platform Engineer ")).toEqual({
      kind: "role",
      input_text: "Platform Engineer",
      normalized_text: null,
      taxonomy_id: null,
      source: "unknown",
      confidence: "unknown",
      accepted_by_user: false,
    });
    expect(buildUnknownSkillTaxonomy("TypeScript")).toEqual(
      expect.objectContaining({
        kind: "skill",
        input_text: "TypeScript",
        accepted_by_user: false,
        source: "unknown",
      }),
    );
  });
});
