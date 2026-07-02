/**
 * Popular job roles browser — full-time careers by educational stream
 * and part-time / odd-job listings. Selecting a role auto-loads prep flow.
 */

import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GraduationCap, Clock, Briefcase, Loader2, Sparkles } from "lucide-react";
import { Badge } from "../ui/Badge";
import {
  type EmploymentCategory,
  type PopularJobRole,
  getStreamsForCategory,
  getRolesForStream,
} from "../../lib/popularJobRoles";

interface PopularJobRolesPanelProps {
  onSelectRole: (role: PopularJobRole) => void;
  selectingRoleId?: string | null;
}

export function PopularJobRolesPanel({ onSelectRole, selectingRoleId }: PopularJobRolesPanelProps) {
  const [category, setCategory] = useState<EmploymentCategory>("full_time");
  const streams = useMemo(() => getStreamsForCategory(category), [category]);
  const [activeStreamId, setActiveStreamId] = useState(streams[0]?.id ?? "");

  const activeStream = streams.find((s) => s.id === activeStreamId) ?? streams[0];
  const roles = useMemo(
    () => (activeStream ? getRolesForStream(activeStream.id, category) : []),
    [activeStream, category],
  );

  const switchCategory = (next: EmploymentCategory) => {
    setCategory(next);
    const nextStreams = getStreamsForCategory(next);
    setActiveStreamId(nextStreams[0]?.id ?? "");
  };

  return (
    <div className="feature-glass feature-panel popular-roles-panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        <div>
          <h2 style={{ fontFamily: "var(--font-heading)", fontWeight: 700, fontSize: "1.15rem", marginBottom: "0.35rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <GraduationCap size={18} style={{ color: "var(--accent-violet)" }} />
            Popular job roles
          </h2>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", maxWidth: 560 }}>
            Browse roles across educational streams. Select a role to auto-fill job details — then review, save, and generate your interview pack when you are ready.
          </p>
        </div>
        <div className="popular-roles-panel__category-toggle">
          <button
            type="button"
            className={category === "full_time" ? "popular-roles-panel__cat--active" : ""}
            onClick={() => switchCategory("full_time")}
          >
            <Briefcase size={14} /> Full-time careers
          </button>
          <button
            type="button"
            className={category === "part_time_odd" ? "popular-roles-panel__cat--active" : ""}
            onClick={() => switchCategory("part_time_odd")}
          >
            <Clock size={14} /> Part-time & odd jobs
          </button>
        </div>
      </div>

      <div className="popular-roles-panel__streams" role="tablist">
        {streams.map((stream) => (
          <button
            key={stream.id}
            type="button"
            role="tab"
            aria-selected={activeStreamId === stream.id}
            className={activeStreamId === stream.id ? "popular-roles-panel__stream--active" : ""}
            onClick={() => setActiveStreamId(stream.id)}
          >
            {stream.label}
          </button>
        ))}
      </div>

      {activeStream && (
        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", margin: "0.75rem 0 0.5rem" }}>
          {activeStream.label} · {roles.length} role{roles.length !== 1 ? "s" : ""}
        </p>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={`${category}-${activeStreamId}`}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="popular-roles-panel__grid"
        >
          {roles.map((r) => {
            const loading = selectingRoleId === r.id;
            return (
              <button
                key={r.id}
                type="button"
                className={`popular-roles-panel__role${loading ? " popular-roles-panel__role--loading" : ""}`}
                onClick={() => onSelectRole(r)}
                disabled={!!selectingRoleId}
              >
                <span style={{ fontWeight: 600, fontSize: "0.8rem", textAlign: "left" }}>{r.title}</span>
                <span style={{ fontSize: "0.65rem", color: "var(--text-secondary)", marginTop: "0.25rem", textAlign: "left", lineHeight: 1.35 }}>
                  {r.skills.slice(0, 3).join(" · ")}
                </span>
                <div style={{ display: "flex", gap: "0.25rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
                  <Badge color={category === "part_time_odd" ? "amber" : "violet"} size="sm">
                    {r.employment_type}
                  </Badge>
                </div>
                {loading && (
                  <span className="popular-roles-panel__loading">
                    <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
                    Preparing…
                  </span>
                )}
              </button>
            );
          })}
        </motion.div>
      </AnimatePresence>

      {!roles.length && (
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", padding: "1rem 0" }}>No roles in this stream yet.</p>
      )}

      <p style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "1rem", display: "flex", alignItems: "center", gap: "0.35rem" }}>
        <Sparkles size={12} />
        Selecting a role fills the job form only. Click <strong>Generate interview pack</strong> when you are ready — company name is optional.
      </p>
    </div>
  );
}
