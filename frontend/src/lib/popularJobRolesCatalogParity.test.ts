// Frontend tsconfig omits @types/node and B5.3 forbids package.json / tsconfig
// edits. Vitest runs these imports on Node; suppress compile-time module errors.

// @ts-expect-error Node builtin unavailable in frontend DOM tsconfig types
import { readFileSync } from "node:fs";
// @ts-expect-error Node builtin unavailable in frontend DOM tsconfig types
import { dirname, resolve } from "node:path";
// @ts-expect-error Node builtin unavailable in frontend DOM tsconfig types
import { fileURLToPath } from "node:url";

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ALL_POPULAR_ROLES,
  type PopularJobRole,
} from "./popularJobRoles";

type JsonCatalogRole = {
  id: string;
  title: string;
  stream_id: string;
  category: string;
  skills: string[];
  responsibilities: string[];
  requirements: string[];
  employment_type: string;
  experience_level: string;
};

const MIRRORED_JSON_KEYS = [
  "category",
  "employment_type",
  "experience_level",
  "id",
  "requirements",
  "responsibilities",
  "skills",
  "stream_id",
  "title",
] as const;

const testDirectory = dirname(fileURLToPath(import.meta.url));

const backendCatalogPath = resolve(
  testDirectory,
  "../../../backend/app/data/popular_roles_catalog.json",
);

const jsonCatalog = JSON.parse(
  readFileSync(backendCatalogPath, "utf8"),
) as JsonCatalogRole[];

const projectRuntimeRole = (
  role: PopularJobRole,
): JsonCatalogRole => ({
  id: role.id,
  title: role.title,
  stream_id: role.streamId,
  category: role.category,
  skills: [...role.skills],
  responsibilities: [...role.responsibilities],
  requirements: [...role.requirements],
  employment_type: role.employment_type,
  experience_level: role.experience_level,
});

const runtimeMirror = ALL_POPULAR_ROLES.map(projectRuntimeRole);

describe("Popular Role runtime TS to backend JSON parity", () => {
  it("keeps both catalogs non-empty and equal in count", () => {
    expect(runtimeMirror.length).toBeGreaterThan(0);
    expect(jsonCatalog.length).toBe(runtimeMirror.length);
  });

  it("keeps identical role ID sets", () => {
    const runtimeIds = [...runtimeMirror.map((role) => role.id)].sort();
    const jsonIds = [...jsonCatalog.map((role) => role.id)].sort();

    expect(jsonIds).toEqual(runtimeIds);
  });

  it("keeps mirrored fields equal by canonical role ID", () => {
    const jsonById = new Map(
      jsonCatalog.map((role) => [role.id, role]),
    );

    for (const runtimeRole of runtimeMirror) {
      expect(
        jsonById.get(runtimeRole.id),
        `mirror drift for role ${runtimeRole.id}`,
      ).toEqual(runtimeRole);
    }
  });

  it("preserves role order as the sync contract", () => {
    expect(
      jsonCatalog.map((role) => role.id),
    ).toEqual(
      runtimeMirror.map((role) => role.id),
    );
  });

  it("keeps the JSON mirror schema limited to contractual mirrored fields", () => {
    for (const role of jsonCatalog) {
      expect(
        Object.keys(role).sort(),
        `unexpected JSON mirror keys for ${role.id}`,
      ).toEqual([...MIRRORED_JSON_KEYS].sort());
    }
  });

  it("matches the full ordered runtime projection exactly", () => {
    expect(jsonCatalog).toEqual(runtimeMirror);
  });
});
