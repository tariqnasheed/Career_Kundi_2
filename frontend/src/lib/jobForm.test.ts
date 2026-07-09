import {
  describe,
  expect,
  it,
} from "vitest";

import {
  EMPTY_JOB_FORM,
  formToSavePayload,
  jobToForm,
} from "./jobForm";
import type {
  SavedJobRead,
} from "../types/api";


function savedJobWithRemote(
  isRemote: boolean | null,
): SavedJobRead {
  return {
    id: "job-1",
    title: "Platform Engineer",
    company_name: null,
    company_url: null,
    location: null,
    employment_type: null,
    is_remote: isRemote,
    salary_min: null,
    salary_max: null,
    salary_currency: null,
    description_raw: null,
    responsibilities: [],
    requirements: [],
    benefits: [],
    extracted_skills: [],
    company_profile: {},
    source_url: null,
    source_site: null,
    import_method: "manual",
    verification_status: "unverified",
    verification_sources: [],
    status: "saved",
    match_score: null,
    interview_pack_confidence: null,
    interview_pack_generated_at: null,
    has_interview_pack: false,
    created_at: "2026-07-09T00:00:00Z",
    updated_at: "2026-07-09T00:00:00Z",
  };
}


describe("job form remote semantics", () => {
  it("preserves null when loading a saved job", () => {
    const form = jobToForm(
      savedJobWithRemote(null),
    );

    expect(form.is_remote).toBeNull();
  });

  it("omits is_remote from an untouched null payload", () => {
    const form = jobToForm(
      savedJobWithRemote(null),
    );

    const payload = formToSavePayload({
      ...form,
      title: "Updated title",
    });

    expect(
      Object.prototype.hasOwnProperty.call(
        payload,
        "is_remote",
      ),
    ).toBe(false);
  });

  it("omits is_remote for a new untouched manual form", () => {
    const payload = formToSavePayload({
      ...EMPTY_JOB_FORM,
      title: "New role",
    });

    expect(
      Object.prototype.hasOwnProperty.call(
        payload,
        "is_remote",
      ),
    ).toBe(false);
  });

  it("includes explicit false", () => {
    const payload = formToSavePayload({
      ...EMPTY_JOB_FORM,
      title: "On-site role",
      is_remote: false,
    });

    expect(payload).toHaveProperty(
      "is_remote",
      false,
    );
  });

  it("includes explicit true", () => {
    const payload = formToSavePayload({
      ...EMPTY_JOB_FORM,
      title: "Remote role",
      is_remote: true,
    });

    expect(payload).toHaveProperty(
      "is_remote",
      true,
    );
  });

  it("preserves existing false and true through jobToForm", () => {
    expect(
      jobToForm(
        savedJobWithRemote(false),
      ).is_remote,
    ).toBe(false);

    expect(
      jobToForm(
        savedJobWithRemote(true),
      ).is_remote,
    ).toBe(true);
  });
});
