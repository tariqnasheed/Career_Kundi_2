import {
  describe,
  expect,
  it,
} from "vitest";

import {
  ALL_POPULAR_ROLES,
  popularRoleToForm,
} from "./popularJobRoles";
import {
  resolvePendingCreateSavePayload,
} from "./pendingCreateSavePayload";

const roleById = (id: string) => {
  const role = ALL_POPULAR_ROLES.find((candidate) => candidate.id === id);

  if (!role) {
    throw new Error(`Popular Role not found: ${id}`);
  }

  return role;
};

describe("Popular Role form truthfulness", () => {
  it("leaves unsupported vacancy facts unknown across every role", () => {
    for (const role of ALL_POPULAR_ROLES) {
      const form = popularRoleToForm(role);

      expect(form.location, `${role.id}: location`).toBe("");
      expect(form.benefits, `${role.id}: benefits`).toBe("");
      expect(
        form.salary_currency,
        `${role.id}: salary_currency`,
      ).toBe("");
      expect(form.is_remote, `${role.id}: is_remote`).toBeNull();
    }
  });

  it("saves unknown vacancy facts honestly for a full-time role", () => {
    const form = popularRoleToForm(roleById("ft-software-eng"));
    const payload = resolvePendingCreateSavePayload(
      form,
      "popular_role",
    );

    expect(payload.location).toBeNull();
    expect(payload.benefits).toEqual([]);
    expect(payload.salary_currency).toBeNull();
    expect(payload.import_method).toBe("popular_role");
    expect(
      Object.prototype.hasOwnProperty.call(payload, "is_remote"),
    ).toBe(false);
  });

  it("saves unknown vacancy facts honestly for a part-time role", () => {
    const form = popularRoleToForm(roleById("pt-barista"));
    const payload = resolvePendingCreateSavePayload(
      form,
      "popular_role",
    );

    expect(payload.location).toBeNull();
    expect(payload.benefits).toEqual([]);
    expect(payload.salary_currency).toBeNull();
    expect(payload.import_method).toBe("popular_role");
    expect(
      Object.prototype.hasOwnProperty.call(payload, "is_remote"),
    ).toBe(false);
  });

  it("preserves role-specific catalog content for full-time templates", () => {
    const role = roleById("ft-software-eng");
    const form = popularRoleToForm(role);

    expect(form.title).toBe(role.title);
    expect(form.employment_type).toBe(role.employment_type);
    expect(form.experience_level).toBe(role.experience_level);
    expect(form.description_raw).toBe(role.description);
    expect(form.responsibilities).toBe(
      role.responsibilities.join("\n"),
    );
    expect(form.requirements).toBe(
      role.requirements.join("\n"),
    );
    expect(form.skills).toBe(role.skills.join(", "));
  });

  it("preserves role-specific catalog content for part-time templates", () => {
    const role = roleById("pt-barista");
    const form = popularRoleToForm(role);

    expect(form.title).toBe(role.title);
    expect(form.employment_type).toBe(role.employment_type);
    expect(form.experience_level).toBe(role.experience_level);
    expect(form.description_raw).toBe(role.description);
    expect(form.responsibilities).toBe(
      role.responsibilities.join("\n"),
    );
    expect(form.requirements).toBe(
      role.requirements.join("\n"),
    );
    expect(form.skills).toBe(role.skills.join(", "));
  });
});
