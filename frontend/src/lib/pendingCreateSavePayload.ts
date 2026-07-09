import type { JobFormState } from "./jobForm";
import { formToSavePayload } from "./jobForm";
import { savePayloadFromPopularRole } from "./popularJobRoles";

export type PendingCreateOrigin = "popular_role" | null;

export function resolvePendingCreateSavePayload(
  form: JobFormState,
  origin: PendingCreateOrigin,
): Record<string, unknown> {
  return origin === "popular_role"
    ? savePayloadFromPopularRole(form)
    : formToSavePayload(form);
}
