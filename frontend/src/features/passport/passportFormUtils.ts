/**
 * passportFormUtils.ts — pure helpers for Passport F5 editors.
 * No React imports. Does not mutate Passport aggregates in place.
 */

import type { ApiError } from "@/types/api";

export function emptyToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function dedupeCaseInsensitive(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const raw of values) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(trimmed);
  }
  return result;
}

export function splitLines(value: string): string[] {
  return dedupeCaseInsensitive(value.split(/\r?\n/));
}

export function joinLines(values: string[] | null | undefined): string {
  return (values ?? []).join("\n");
}

export function splitCommaList(value: string): string[] {
  return dedupeCaseInsensitive(value.split(","));
}

export function joinCommaList(values: string[] | null | undefined): string {
  return (values ?? []).join(", ");
}

export function normalizeDateInput(
  value: string | null | undefined,
): string {
  if (!value) return "";
  const trimmed = value.trim();
  if (!trimmed) return "";
  // Accept YYYY-MM-DD or ISO; keep date portion for input[type=date]
  if (/^\d{4}-\d{2}-\d{2}/.test(trimmed)) {
    return trimmed.slice(0, 10);
  }
  return trimmed;
}

export function validateDateOrder(
  startDate: string | null,
  endDate: string | null,
  isCurrent: boolean,
): string | null {
  if (isCurrent) return null;
  if (!startDate || !endDate) return null;
  if (endDate < startDate) {
    return "End date must be on or after the start date.";
  }
  return null;
}

export function isConflictError(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const maybe = error as Partial<ApiError>;
  return maybe.code === "CONFLICT";
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== "object") return fallback;
  const maybe = error as Partial<ApiError>;
  if (typeof maybe.message === "string" && maybe.message.trim()) {
    return maybe.message;
  }
  return fallback;
}

export function looksLikeHttpUrl(value: string | null): boolean {
  if (!value) return true;
  return /^https?:\/\//i.test(value);
}
