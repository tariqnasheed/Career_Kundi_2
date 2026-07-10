/**
 * PlatformPage.tsx
 * ================
 * Minimal Platform Foundation shell (0050-PF11-S1).
 * Lists/creates Career Subjects and subject-scoped Goals via PF8 APIs.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Layers, Plus, Target, Info } from "lucide-react";
import { platformApi } from "../lib/api";
import type { ApiError, PlatformGoalCreate, PlatformSubjectRead } from "../types/api";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Input, Textarea } from "../components/ui/Input";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";

const GOAL_KINDS = [
  "career",
  "education",
  "job_search",
  "skill_development",
  "migration",
  "public_service",
  "financial",
  "personal",
  "other",
] as const;

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function shortId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 8)}…` : id;
}

export default function PlatformPage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [goalForm, setGoalForm] = useState<PlatformGoalCreate>({
    goal_kind: "career",
    title: "",
    description: "",
    status: "active",
  });

  const subjectsQuery = useQuery({
    queryKey: ["platform", "subjects"],
    queryFn: () => platformApi.listPlatformSubjects(),
  });

  const goalsQuery = useQuery({
    queryKey: ["platform", "goals", selectedSubjectId],
    queryFn: () => platformApi.listPlatformGoals(selectedSubjectId!),
    enabled: Boolean(selectedSubjectId),
  });

  const createSubject = useMutation({
    mutationFn: () => platformApi.createPlatformSubject(),
    onSuccess: (subject) => {
      addToast({ type: "success", message: "Career Subject created." });
      qc.invalidateQueries({ queryKey: ["platform", "subjects"] });
      setSelectedSubjectId(subject.id);
    },
    onError: (err: ApiError) => {
      addToast({
        type: "error",
        message: err.message || "Could not create Career Subject.",
      });
    },
  });

  const createGoal = useMutation({
    mutationFn: () => {
      if (!selectedSubjectId) throw new Error("No subject selected");
      return platformApi.createPlatformGoal(selectedSubjectId, {
        goal_kind: goalForm.goal_kind,
        title: goalForm.title.trim(),
        description: goalForm.description?.trim() || null,
        status: goalForm.status || "active",
      });
    },
    onSuccess: () => {
      addToast({ type: "success", message: "Goal created." });
      setGoalForm((prev) => ({ ...prev, title: "", description: "" }));
      qc.invalidateQueries({ queryKey: ["platform", "goals", selectedSubjectId] });
    },
    onError: (err: ApiError) => {
      addToast({
        type: "error",
        message: err.message || "Could not create Goal.",
      });
    },
  });

  const selectedSubject: PlatformSubjectRead | undefined =
    subjectsQuery.data?.find((s) => s.id === selectedSubjectId);

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "0.5rem 0 2rem" }}>
      <header style={{ marginBottom: "1.75rem" }}>
        <p
          style={{
            fontSize: "0.75rem",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: "var(--text-secondary)",
            marginBottom: "0.35rem",
          }}
        >
          Foundation preview
        </p>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 800, margin: 0 }}>
          CareerKundi Platform Foundation
        </h1>
        <p
          style={{
            marginTop: "0.5rem",
            color: "var(--text-secondary)",
            fontSize: "0.95rem",
            maxWidth: 640,
            lineHeight: 1.5,
          }}
        >
          Manage the foundation records CareerKundi uses to reason about a career
          journey.
        </p>
      </header>

      {/* Foundation status */}
      <Card variant="elevated" style={{ marginBottom: "1.5rem" }}>
        <CardHeader>
          <CardTitle style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Info size={18} />
            Foundation status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: 0, color: "var(--text-secondary)", lineHeight: 1.55, fontSize: "0.9rem" }}>
            This is an early foundation shell. Claims, evidence, recommendations,
            privacy controls, and opportunity intelligence will be added in later
            phases.
          </p>
        </CardContent>
      </Card>

      {/* Career Subjects */}
      <Card style={{ marginBottom: "1.5rem" }}>
        <CardHeader
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "1rem",
            flexWrap: "wrap",
          }}
        >
          <CardTitle style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Layers size={18} />
            Career Subjects
          </CardTitle>
          <Button
            size="sm"
            onClick={() => createSubject.mutate()}
            disabled={createSubject.isPending}
            leftIcon={<Plus size={14} />}
          >
            {createSubject.isPending ? "Creating…" : "Create Career Subject"}
          </Button>
        </CardHeader>
        <CardContent>
          {subjectsQuery.isLoading && (
            <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
              <Spinner />
            </div>
          )}

          {subjectsQuery.isError && (
            <p role="alert" style={{ color: "var(--danger, #ef4444)", margin: 0 }}>
              {(subjectsQuery.error as unknown as ApiError)?.message ||
                "Could not load Career Subjects. Sign in again if your session expired."}
            </p>
          )}

          {subjectsQuery.isSuccess && subjectsQuery.data.length === 0 && (
            <p style={{ color: "var(--text-secondary)", margin: 0 }}>
              No Career Subjects yet. Create one to start attaching Goals.
            </p>
          )}

          {subjectsQuery.isSuccess && subjectsQuery.data.length > 0 && (
            <ul
              style={{
                listStyle: "none",
                margin: 0,
                padding: 0,
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              {subjectsQuery.data.map((subject) => {
                const active = subject.id === selectedSubjectId;
                return (
                  <li key={subject.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedSubjectId(subject.id)}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "0.875rem 1rem",
                        borderRadius: 12,
                        border: active
                          ? "1px solid var(--accent-violet)"
                          : "1px solid var(--border-subtle)",
                        background: active
                          ? "color-mix(in srgb, var(--accent-violet) 12%, transparent)"
                          : "var(--bg-overlay)",
                        cursor: "pointer",
                        color: "inherit",
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
                        Subject {shortId(subject.id)}
                      </div>
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-secondary)",
                          marginTop: "0.35rem",
                          lineHeight: 1.4,
                        }}
                      >
                        Created {formatDate(subject.created_at)}
                        {" · "}
                        Updated {formatDate(subject.updated_at)}
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Goals */}
      <Card>
        <CardHeader>
          <CardTitle style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Target size={18} />
            Goals
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedSubjectId && (
            <p style={{ color: "var(--text-secondary)", margin: 0 }}>
              Select a Career Subject to view and create Goals.
            </p>
          )}

          {selectedSubject && (
            <div
              style={{
                marginBottom: "1.25rem",
                padding: "0.75rem 1rem",
                borderRadius: 10,
                background: "var(--bg-overlay)",
                border: "1px solid var(--border-subtle)",
                fontSize: "0.85rem",
              }}
            >
              <div style={{ fontWeight: 600 }}>Selected subject</div>
              <div style={{ color: "var(--text-secondary)", marginTop: 4 }}>
                ID: {selectedSubject.id}
              </div>
              <div style={{ color: "var(--text-secondary)", marginTop: 2 }}>
                Created {formatDate(selectedSubject.created_at)}
              </div>
            </div>
          )}

          {selectedSubjectId && goalsQuery.isLoading && (
            <div style={{ display: "flex", justifyContent: "center", padding: "1.5rem" }}>
              <Spinner />
            </div>
          )}

          {selectedSubjectId && goalsQuery.isError && (
            <p role="alert" style={{ color: "var(--danger, #ef4444)", margin: "0 0 1rem" }}>
              {(goalsQuery.error as unknown as ApiError)?.message ||
                "Could not load Goals for this subject."}
            </p>
          )}

          {selectedSubjectId && goalsQuery.isSuccess && goalsQuery.data.length === 0 && (
            <p style={{ color: "var(--text-secondary)", margin: "0 0 1.25rem" }}>
              No Goals yet for this subject.
            </p>
          )}

          {selectedSubjectId && goalsQuery.isSuccess && goalsQuery.data.length > 0 && (
            <ul
              style={{
                listStyle: "none",
                margin: "0 0 1.5rem",
                padding: 0,
                display: "flex",
                flexDirection: "column",
                gap: "0.65rem",
              }}
            >
              {goalsQuery.data.map((goal) => (
                <li
                  key={goal.id}
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: 10,
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-overlay)",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{goal.title}</div>
                  <div
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--text-secondary)",
                      marginTop: 4,
                    }}
                  >
                    {goal.goal_kind} · {goal.status}
                    {goal.description ? ` · ${goal.description}` : ""}
                  </div>
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "var(--text-secondary)",
                      marginTop: 4,
                    }}
                  >
                    Created {formatDate(goal.created_at)}
                  </div>
                </li>
              ))}
            </ul>
          )}

          {selectedSubjectId && (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!goalForm.title.trim()) {
                  addToast({ type: "error", message: "Goal title is required." });
                  return;
                }
                createGoal.mutate();
              }}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.85rem",
                paddingTop: "0.25rem",
                borderTop: "1px solid var(--border-subtle)",
              }}
            >
              <p style={{ margin: "0.5rem 0 0", fontWeight: 600, fontSize: "0.9rem" }}>
                Create Goal
              </p>
              <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.8rem" }}>
                Kind
                <select
                  value={goalForm.goal_kind}
                  onChange={(e) =>
                    setGoalForm((prev) => ({ ...prev, goal_kind: e.target.value }))
                  }
                  style={{
                    padding: "0.55rem 0.75rem",
                    borderRadius: 8,
                    border: "1px solid var(--border-subtle)",
                    background: "var(--bg-elevated)",
                    color: "inherit",
                  }}
                >
                  {GOAL_KINDS.map((kind) => (
                    <option key={kind} value={kind}>
                      {kind}
                    </option>
                  ))}
                </select>
              </label>
              <Input
                label="Title"
                fullWidth
                value={goalForm.title}
                onChange={(e) =>
                  setGoalForm((prev) => ({ ...prev, title: e.target.value }))
                }
                placeholder="e.g. Land a backend engineering role"
                required
              />
              <Textarea
                label="Description (optional)"
                fullWidth
                value={goalForm.description ?? ""}
                onChange={(e) =>
                  setGoalForm((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="Short context for this goal"
                rows={3}
              />
              <div>
                <Button
                  type="submit"
                  disabled={createGoal.isPending}
                  leftIcon={<Plus size={14} />}
                >
                  {createGoal.isPending ? "Creating…" : "Create Goal"}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
