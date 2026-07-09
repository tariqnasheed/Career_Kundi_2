import {
  describe,
  expect,
  it,
} from "vitest";

import { EMPTY_JOB_FORM } from "./jobForm";
import {
  ALL_POPULAR_ROLES,
  popularRoleToForm,
} from "./popularJobRoles";
import { resolvePendingCreateSavePayload } from "./pendingCreateSavePayload";


describe("resolvePendingCreateSavePayload", () => {
  it("sets import_method popular_role for popular pending origin", () => {
    const role = ALL_POPULAR_ROLES[0];
    if (!role) {
      throw new Error("expected at least one popular role");
    }
    const form = popularRoleToForm(role);
    const payload = resolvePendingCreateSavePayload(form, "popular_role");

    expect(
      Object.prototype.hasOwnProperty.call(payload, "import_method"),
    ).toBe(true);
    expect(payload.import_method).toBe("popular_role");
  });

  it("sets import_method manual when pending origin is null", () => {
    const form = {
      ...EMPTY_JOB_FORM,
      title: "Manual Role",
    };
    const payload = resolvePendingCreateSavePayload(form, null);

    expect(payload.import_method).toBe("manual");
  });

  it("omits is_remote when popular create form has null remote", () => {
    const role = ALL_POPULAR_ROLES.find((candidate) => candidate.id === "ft-software-eng");
    if (!role) {
      throw new Error("ft-software-eng not found");
    }
    const form = popularRoleToForm(role);

    expect(form.is_remote).toBeNull();

    const payload = resolvePendingCreateSavePayload(form, "popular_role");

    expect(
      Object.prototype.hasOwnProperty.call(payload, "is_remote"),
    ).toBe(false);
  });

  it("does not mutate the input form when resolving popular payload", () => {
    const role = ALL_POPULAR_ROLES.find((candidate) => candidate.id === "pt-barista");
    if (!role) {
      throw new Error("pt-barista not found");
    }
    const form = popularRoleToForm(role);
    const before = {
      is_remote: form.is_remote,
      title: form.title,
      location: form.location,
      employment_type: form.employment_type,
    };

    resolvePendingCreateSavePayload(form, "popular_role");

    expect(form.is_remote).toBeNull();
    expect(form.title).toBe(before.title);
    expect(form.location).toBe(before.location);
    expect(form.employment_type).toBe(before.employment_type);
  });

  it("preserves explicit false is_remote for null-origin payload", () => {
    const form = {
      ...EMPTY_JOB_FORM,
      title: "Onsite Role",
      is_remote: false,
    };
    const payload = resolvePendingCreateSavePayload(form, null);

    expect(
      Object.prototype.hasOwnProperty.call(payload, "is_remote"),
    ).toBe(true);
    expect(payload.is_remote).toBe(false);
  });
});
