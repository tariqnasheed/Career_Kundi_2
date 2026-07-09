import {
  Briefcase,
  MapPin,
  Search,
} from "lucide-react";

import {
  hasActiveSavedJobSearchFilter,
  type SavedJobSearchFilters,
} from "../../lib/savedJobSearchFilters";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";


export type VisibleSavedJobSearchFilters = Omit<
  SavedJobSearchFilters,
  "remote"
> & {
  remote: true | undefined;
};


export interface SavedJobFiltersProps {
  filters: VisibleSavedJobSearchFilters;
  onChange: (
    filters: VisibleSavedJobSearchFilters,
  ) => void;
  onClearAll: () => void;
}


export function SavedJobFilters({
  filters,
  onChange,
  onClearAll,
}: SavedJobFiltersProps) {
  const hasActiveFilters = (
    hasActiveSavedJobSearchFilter(
      filters,
    )
  );

  return (
    <section
      aria-label="Saved job filters"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: (
            "repeat(auto-fit, minmax(180px, 1fr))"
          ),
          gap: "0.75rem",
        }}
      >
        <Input
          label="Keywords"
          placeholder="Title, company, or description"
          value={filters.q}
          onChange={(event) => {
            onChange({
              ...filters,
              q: event.target.value,
            });
          }}
          leftIcon={<Search size={14} />}
          fullWidth
        />

        <Input
          label="Location"
          placeholder="London, Berlin, Remote"
          value={filters.location}
          onChange={(event) => {
            onChange({
              ...filters,
              location: event.target.value,
            });
          }}
          leftIcon={<MapPin size={14} />}
          fullWidth
        />

        <Input
          label="Employment type"
          placeholder="Full-time, Contract"
          hint="Matches the exact saved employment-type value."
          value={filters.employmentType}
          onChange={(event) => {
            onChange({
              ...filters,
              employmentType: event.target.value,
            });
          }}
          leftIcon={<Briefcase size={14} />}
          fullWidth
        />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.75rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <p
            id="saved-job-remote-filter-label"
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: "var(--text-secondary)",
              marginBottom: "0.4rem",
            }}
          >
            Remote status
          </p>

          <div
            role="group"
            aria-labelledby="saved-job-remote-filter-label"
            style={{
              display: "flex",
              gap: "0.35rem",
            }}
          >
            <Button
              type="button"
              variant={
                filters.remote === undefined
                  ? "primary"
                  : "secondary"
              }
              size="sm"
              aria-pressed={
                filters.remote === undefined
              }
              onClick={() => {
                onChange({
                  ...filters,
                  remote: undefined,
                });
              }}
            >
              Any
            </Button>

            <Button
              type="button"
              variant={
                filters.remote === true
                  ? "primary"
                  : "secondary"
              }
              size="sm"
              aria-pressed={
                filters.remote === true
              }
              onClick={() => {
                onChange({
                  ...filters,
                  remote: true,
                });
              }}
            >
              Remote only
            </Button>
          </div>
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={!hasActiveFilters}
          onClick={onClearAll}
        >
          Clear all
        </Button>
      </div>
    </section>
  );
}
