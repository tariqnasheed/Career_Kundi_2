import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ALL_POPULAR_ROLES,
  EDUCATION_STREAMS,
  getStreamsForCategory,
} from "./popularJobRoles";

// PART_TIME_STREAMS is module-private in popularJobRoles.ts; use the exported
// getStreamsForCategory("part_time_odd") accessor instead of exporting it.

const normalizeText = (value: string): string =>
  value.trim().toLowerCase().replace(/\s+/g, " ");

const normalizedDuplicates = (values: string[]): string[] => {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const value of values) {
    const normalized = normalizeText(value);
    if (seen.has(normalized)) {
      duplicates.add(normalized);
    }
    seen.add(normalized);
  }

  return [...duplicates].sort();
};

const exactDuplicates = (values: string[]): string[] => {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }

  return [...duplicates].sort();
};

const blankEntries = (values: string[]): string[] =>
  values.filter((value) => value.trim().length === 0);

describe("Popular Role catalog structural integrity", () => {
  it("contains at least one role without freezing the catalog at 78", () => {
    expect(ALL_POPULAR_ROLES.length).toBeGreaterThan(0);
  });

  it("has unique exact and normalized role IDs", () => {
    const ids = ALL_POPULAR_ROLES.map((role) => role.id);

    expect(exactDuplicates(ids)).toEqual([]);
    expect(normalizedDuplicates(ids)).toEqual([]);
  });

  it("has unique exact and normalized role titles", () => {
    const titles = ALL_POPULAR_ROLES.map((role) => role.title);

    expect(exactDuplicates(titles)).toEqual([]);
    expect(normalizedDuplicates(titles)).toEqual([]);
  });

  it("uses only declared stream IDs", () => {
    const fullTimeStreamIds = new Set(
      EDUCATION_STREAMS.map((stream) => stream.id),
    );
    const partTimeStreamIds = new Set(
      getStreamsForCategory("part_time_odd").map((stream) => stream.id),
    );

    for (const role of ALL_POPULAR_ROLES) {
      const allowedStreams = role.category === "full_time"
        ? fullTimeStreamIds
        : partTimeStreamIds;

      expect(
        allowedStreams.has(role.streamId),
        `${role.id} references invalid stream ${role.streamId}`,
      ).toBe(true);
    }
  });

  it("keeps role ID prefixes aligned with category", () => {
    for (const role of ALL_POPULAR_ROLES) {
      const expectedPrefix = role.category === "full_time"
        ? "ft-"
        : "pt-";

      expect(
        role.id.startsWith(expectedPrefix),
        `${role.id} must start with ${expectedPrefix}`,
      ).toBe(true);
    }
  });

  it("keeps required scalar fields non-blank", () => {
    for (const role of ALL_POPULAR_ROLES) {
      expect(role.id.trim(), `${role.id}: blank id`).not.toBe("");
      expect(role.title.trim(), `${role.id}: blank title`).not.toBe("");
      expect(role.streamId.trim(), `${role.id}: blank streamId`).not.toBe("");
      expect(
        role.employment_type.trim(),
        `${role.id}: blank employment_type`,
      ).not.toBe("");
      expect(
        role.experience_level.trim(),
        `${role.id}: blank experience_level`,
      ).not.toBe("");
      expect(
        role.description.trim(),
        `${role.id}: blank description`,
      ).not.toBe("");
    }
  });

  it("keeps required arrays non-empty and free of blank entries", () => {
    for (const role of ALL_POPULAR_ROLES) {
      const arrays = {
        skills: role.skills,
        responsibilities: role.responsibilities,
        requirements: role.requirements,
      };

      for (const [field, values] of Object.entries(arrays)) {
        expect(
          values.length,
          `${role.id}: ${field} must not be empty`,
        ).toBeGreaterThan(0);

        expect(
          blankEntries(values),
          `${role.id}: ${field} contains blank entries`,
        ).toEqual([]);
      }
    }
  });

  it("has no normalized duplicates within role arrays", () => {
    for (const role of ALL_POPULAR_ROLES) {
      const arrays = {
        skills: role.skills,
        responsibilities: role.responsibilities,
        requirements: role.requirements,
      };

      for (const [field, values] of Object.entries(arrays)) {
        expect(
          normalizedDuplicates(values),
          `${role.id}: duplicate entries in ${field}`,
        ).toEqual([]);
      }
    }
  });

  it("keeps stream IDs unique within each stream catalog", () => {
    const fullTimeIds = EDUCATION_STREAMS.map((stream) => stream.id);
    const partTimeIds = getStreamsForCategory("part_time_odd").map(
      (stream) => stream.id,
    );

    expect(exactDuplicates(fullTimeIds)).toEqual([]);
    expect(normalizedDuplicates(fullTimeIds)).toEqual([]);
    expect(exactDuplicates(partTimeIds)).toEqual([]);
    expect(normalizedDuplicates(partTimeIds)).toEqual([]);
  });
});
