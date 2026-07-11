/**
 * Persistent default CV selector for job search & application workflows.
 */

import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { FileText, Star } from "lucide-react";
import { cvApi } from "../../lib/api";
import { Button } from "../ui/Button";
import type { ApiError } from "../../types/api";

const STORAGE_KEY = "ck_default_cv_id";

export function getDefaultCvId(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

export function setDefaultCvId(id: string) {
  localStorage.setItem(STORAGE_KEY, id);
}

interface DefaultCVSelectorProps {
  value: string;
  onChange: (id: string) => void;
}

export function DefaultCVSelector({ value, onChange }: DefaultCVSelectorProps) {
  const { data: cvs, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["cvs"],
    queryFn: () => cvApi.list(),
  });

  if (isLoading) return <div className="default-cv-bar feature-glass skeleton" style={{ height: 56 }} />;

  if (isError) {
    return (
      <div className="default-cv-bar feature-glass" role="alert">
        <FileText size={18} style={{ color: "var(--accent-cyan)", flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>
            Default CV for applications
          </p>
          <p style={{ fontSize: "0.8rem", color: "var(--danger, #ef4444)" }}>
            {(error as unknown as ApiError | undefined)?.message || "We couldn't load saved CVs. Please try again."}
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="default-cv-bar feature-glass">
      <FileText size={18} style={{ color: "var(--accent-cyan)", flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>
          Default CV for applications
        </p>
        {cvs?.length ? (
          <select value={value} onChange={(e) => { onChange(e.target.value); setDefaultCvId(e.target.value); }} aria-label="Select default CV">
            {cvs.map((cv) => (
              <option key={cv.id} value={cv.id}>{cv.name || cv.template}</option>
            ))}
          </select>
        ) : (
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            No saved CVs yet — <Link to="/cv-builder">create a draft in CV Builder</Link>
          </p>
        )}
      </div>
      {value && (
        <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: "0.7rem", color: "var(--accent-amber)" }}>
          <Star size={12} fill="currentColor" /> Active default
        </span>
      )}
      <Link to="/cv-builder">
        <Button variant="secondary" size="sm">New CV</Button>
      </Link>
    </div>
  );
}
