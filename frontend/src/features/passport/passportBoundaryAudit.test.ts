/**
 * passportBoundaryAudit.test.ts — 0052-F8 static boundary audit.
 * Reads source as text. No React. No network.
 */
// @ts-nocheck — Node fs/path used only in Vitest; excluded from app runtime.

import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(__dirname, "../../..");

function readSrc(rel: string): string {
  return fs.readFileSync(path.join(ROOT, "src", rel), "utf8");
}

const AUDIT_FILES = [
  "features/passport/PassportPage.tsx",
  "features/passport/PassportEvidencePanel.tsx",
  "features/passport/PassportEditForms.tsx",
  "features/passport/passportIntegrationUtils.ts",
  "pages/ProfilePage.tsx",
  "pages/CVBuilderPage.tsx",
  "pages/RoadmapPage.tsx",
  "pages/DashboardPage.tsx",
  "lib/api.ts",
] as const;

const USER_FACING_PAGES = [
  "features/passport/PassportPage.tsx",
  "features/passport/PassportEvidencePanel.tsx",
  "features/passport/PassportEditForms.tsx",
  "features/passport/passportIntegrationUtils.ts",
  "pages/ProfilePage.tsx",
  "pages/CVBuilderPage.tsx",
  "pages/RoadmapPage.tsx",
  "pages/DashboardPage.tsx",
] as const;

const FORBIDDEN_LANGUAGE = [
  "Verified Passport",
  "Official credential",
  "Evidence-backed",
  "Approved Passport",
  "Public Passport",
  "Passport strength",
  "Profile score",
  "Credential wallet",
  "blockchain",
  "DID",
  "share Passport",
  "public profile URL",
] as const;

const INTEGRATION_PAYLOAD_FORBIDDEN = [
  "passport_id",
  "passport_target_id",
  "public_url",
  "sharing",
  "wallet",
  "did",
  "blockchain",
] as const;

const MUTATION_METHODS = [
  "passportApi.patchProfile",
  "passportApi.createExperience",
  "passportApi.patchExperience",
  "passportApi.deleteExperience",
  "passportApi.reorderExperience",
  "passportApi.reorderExperiences",
  "passportApi.createEducation",
  "passportApi.patchEducation",
  "passportApi.deleteEducation",
  "passportApi.reorderEducation",
  "passportApi.createProject",
  "passportApi.patchProject",
  "passportApi.deleteProject",
  "passportApi.reorderProject",
  "passportApi.reorderProjects",
  "passportApi.createSkill",
  "passportApi.patchSkill",
  "passportApi.deleteSkill",
  "passportApi.reorderSkill",
  "passportApi.reorderSkills",
  "passportApi.createCredential",
  "passportApi.patchCredential",
  "passportApi.deleteCredential",
  "passportApi.reorderCredential",
  "passportApi.reorderCredentials",
  "passportApi.createTarget",
  "passportApi.patchTarget",
  "passportApi.deleteTarget",
  "passportApi.reorderTarget",
  "passportApi.reorderTargets",
] as const;

const INTEGRATION_PAGES = [
  "pages/ProfilePage.tsx",
  "pages/CVBuilderPage.tsx",
  "pages/RoadmapPage.tsx",
  "pages/DashboardPage.tsx",
] as const;

const PLATFORM_SUBJECT_PAGES = [
  "features/passport/PassportPage.tsx",
  "features/passport/PassportEditForms.tsx",
  "features/passport/passportIntegrationUtils.ts",
  "pages/ProfilePage.tsx",
  "pages/CVBuilderPage.tsx",
  "pages/RoadmapPage.tsx",
] as const;

describe("0052-F8 Passport boundary audit", () => {
  it("reads all audit source files", () => {
    for (const rel of AUDIT_FILES) {
      expect(readSrc(rel).length).toBeGreaterThan(0);
    }
  });

  it("forbids user-facing Passport/product language on audited pages", () => {
    for (const rel of USER_FACING_PAGES) {
      const src = readSrc(rel);
      for (const phrase of FORBIDDEN_LANGUAGE) {
        if (phrase === "DID") {
          // Acronym only — avoid matching substrings like "Candidate"
          expect(src.match(/\bDID\b/), `${rel} must not contain DID`).toBeNull();
          continue;
        }
        const re = new RegExp(phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i");
        expect(src.match(re), `${rel} must not contain "${phrase}"`).toBeNull();
      }
    }
  });

  it("allows only passportApi.get on Profile/CV/Roadmap/Dashboard", () => {
    for (const rel of INTEGRATION_PAGES) {
      const src = readSrc(rel);
      for (const method of MUTATION_METHODS) {
        expect(src.includes(method), `${rel} must not call ${method}`).toBe(false);
      }
      if (rel !== "pages/DashboardPage.tsx") {
        expect(src.includes("passportApi.get"), `${rel} should read Passport via get`).toBe(
          true,
        );
      } else {
        expect(src.includes("passportApi."), `${rel} must not use passportApi`).toBe(false);
      }
    }
  });

  it("forbids integration ownership leakage payloads on Profile/CV/Roadmap", () => {
    for (const rel of [
      "pages/ProfilePage.tsx",
      "pages/CVBuilderPage.tsx",
      "pages/RoadmapPage.tsx",
      "features/passport/passportIntegrationUtils.ts",
    ] as const) {
      const src = readSrc(rel);
      for (const token of INTEGRATION_PAYLOAD_FORBIDDEN) {
        // "sharing" alone is too broad for comments; require word-ish match for short tokens
        if (token === "did") {
          expect(
            src.match(/\bdid\b/i),
            `${rel} must not contain standalone did`,
          ).toBeNull();
          continue;
        }
        expect(
          src.toLowerCase().includes(token.toLowerCase()),
          `${rel} must not contain ${token}`,
        ).toBe(false);
      }
    }
  });

  it("forbids /platform/subjects in Passport feature and Profile/CV/Roadmap", () => {
    for (const rel of PLATFORM_SUBJECT_PAGES) {
      const src = readSrc(rel);
      expect(src.includes("/platform/subjects"), `${rel} must not call subjects`).toBe(
        false,
      );
    }
  });

  it("forbids verify/approve/reject/share/upload/download controls in Passport evidence panel", () => {
    const src = readSrc("features/passport/PassportEvidencePanel.tsx");
    for (const phrase of [
      "Verify claim",
      "Verify Passport",
      "Verified Passport",
      "Approve",
      "Reject",
      "Publish",
      "Share",
      'type="file"',
      "downloadEvidence",
      "uploadEvidence",
    ]) {
      expect(src.includes(phrase), `panel must not contain ${phrase}`).toBe(
        false,
      );
    }
    expect(src.includes("Request private review")).toBe(true);
    expect(src.includes("Cancel review request")).toBe(true);
    expect(src.includes("reviewRequestApi")).toBe(true);
    expect(
      src.includes("Request intake requires linked private evidence"),
    ).toBe(true);
    expect(
      src.includes("Link private evidence before requesting review."),
    ).toBe(true);
    expect(src.includes("scan not available")).toBe(true);
    expect(src.toLowerCase().includes("malware-scanned")).toBe(true);
    for (const phrase of ["Scan file", "Parse file", "OCR", "AI review"]) {
      expect(src.includes(phrase), `panel must not contain ${phrase}`).toBe(
        false,
      );
    }
  });

  it("documents that api.ts may define Passport mutation clients for /passport only", () => {
    const api = readSrc("lib/api.ts");
    expect(api.includes("passportApi")).toBe(true);
    expect(api.includes("get:")).toBe(true);
  });
});
