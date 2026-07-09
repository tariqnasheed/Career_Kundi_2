import {
  describe,
  expect,
  it,
} from "vitest";

import { formToSavePayload } from "./jobForm";
import {
  ALL_POPULAR_ROLES,
  popularRoleToForm,
} from "./popularJobRoles";


function roleById(id: string) {
  const role = ALL_POPULAR_ROLES.find((candidate) => candidate.id === id);
  if (!role) {
    throw new Error(`Role ${id} not found`);
  }
  return role;
}


describe("popularRoleToForm remote semantics", () => {
  it("returns null is_remote for a representative full-time role", () => {
    const form = popularRoleToForm(roleById("ft-software-eng"));

    expect(form.is_remote).toBeNull();
  });

  it("returns null is_remote for a representative part-time non-admin role", () => {
    const form = popularRoleToForm(roleById("pt-barista"));

    expect(form.is_remote).toBeNull();
  });

  it("returns null is_remote for an admin_remote role", () => {
    const form = popularRoleToForm(roleById("pt-data-entry"));

    expect(form.is_remote).toBeNull();
  });

  it("returns null is_remote for every catalog role", () => {
    for (const role of ALL_POPULAR_ROLES) {
      const form = popularRoleToForm(role);

      expect(form.is_remote).toBeNull();
    }
  });

  it("omits is_remote from save payload for popular role forms", () => {
    const formerlyFalsePayload = formToSavePayload(
      popularRoleToForm(roleById("ft-software-eng")),
    );
    expect(
      Object.prototype.hasOwnProperty.call(
        formerlyFalsePayload,
        "is_remote",
      ),
    ).toBe(false);

    const formerlyTruePayload = formToSavePayload(
      popularRoleToForm(roleById("pt-data-entry")),
    );
    expect(
      Object.prototype.hasOwnProperty.call(
        formerlyTruePayload,
        "is_remote",
      ),
    ).toBe(false);
  });
});
