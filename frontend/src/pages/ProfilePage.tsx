/**
 * ProfilePage.tsx
 * ================
 * Editable career profile — the single source of truth for all AI features.
 * The CV builder, roadmap planner, and job matcher all draw from this data.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { User, Briefcase, GraduationCap, Code, Award, Globe, Save, Plus, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { profileApi } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Input, Textarea } from "../components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Spinner } from "../components/ui/Spinner";
import { useUIStore } from "../store/ui";

// ─── Collapsible section wrapper ──────────────────────────────────────────
function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <Card padding="none" style={{ marginBottom: "1.25rem", overflow: "hidden" }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: "0.75rem",
          padding: "1rem 1.25rem", background: "none", border: "none", cursor: "pointer",
          borderBottom: open ? "1px solid var(--border-subtle)" : "none",
        }}
      >
        <span style={{ color: "var(--accent-violet)" }}>{icon}</span>
        <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", flex: 1, textAlign: "left" }}>{title}</span>
        {open ? <ChevronUp size={15} style={{ color: "var(--text-secondary)" }} /> : <ChevronDown size={15} style={{ color: "var(--text-secondary)" }} />}
      </button>
      {open && <div style={{ padding: "1.25rem" }}>{children}</div>}
    </Card>
  );
}

// ─── Experience editor ────────────────────────────────────────────────────
function ExperienceEditor({ items, onChange }: { items: any[]; onChange: (v: any[]) => void }) {
  const add = () => onChange([...items, { title: "", company: "", start_date: "", end_date: "", bullets: [""] }]);
  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i));
  const set = (i: number, key: string, val: any) => {
    const next = [...items];
    next[i] = { ...next[i], [key]: val };
    onChange(next);
  };
  const setBullet = (i: number, j: number, val: string) => {
    const bullets = [...(items[i].bullets ?? [])];
    bullets[j] = val;
    set(i, "bullets", bullets);
  };

  return (
    <div>
      {items.map((exp, i) => (
        <div key={i} style={{ marginBottom: "1.25rem", padding: "1rem", borderRadius: "12px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <Input label="Job title" value={exp.title} onChange={e => set(i, "title", e.target.value)} fullWidth />
            <Input label="Company" value={exp.company} onChange={e => set(i, "company", e.target.value)} fullWidth />
            <Input label="Start date" value={exp.start_date} onChange={e => set(i, "start_date", e.target.value)} placeholder="Jan 2022" fullWidth />
            <Input label="End date" value={exp.end_date ?? ""} onChange={e => set(i, "end_date", e.target.value)} placeholder="Present" fullWidth />
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>Achievements / bullet points</p>
          {(exp.bullets ?? []).map((b: string, j: number) => (
            <div key={j} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.4rem" }}>
              <Input value={b} onChange={e => setBullet(i, j, e.target.value)} placeholder="• Describe an achievement with measurable impact" fullWidth />
              <Button variant="ghost" size="sm" onClick={() => { const bl = [...(exp.bullets ?? [])]; bl.splice(j, 1); set(i, "bullets", bl); }}>×</Button>
            </div>
          ))}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.5rem" }}>
            <Button variant="ghost" size="sm" onClick={() => set(i, "bullets", [...(exp.bullets ?? []), ""])}>+ Add bullet</Button>
            <Button variant="ghost" size="sm" onClick={() => remove(i)}><Trash2 size={13} /></Button>
          </div>
        </div>
      ))}
      <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} onClick={add}>Add experience</Button>
    </div>
  );
}

// ─── Education editor ─────────────────────────────────────────────────────
function EducationEditor({ items, onChange }: { items: any[]; onChange: (v: any[]) => void }) {
  const add = () => onChange([...items, { degree: "", institution: "", graduation_year: "" }]);
  const remove = (i: number) => onChange(items.filter((_, idx) => idx !== i));
  const set = (i: number, key: string, val: string) => {
    const next = [...items]; next[i] = { ...next[i], [key]: val }; onChange(next);
  };
  return (
    <div>
      {items.map((edu, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "2fr 2fr 1fr auto", gap: "0.75rem", alignItems: "end", marginBottom: "0.75rem" }}>
          <Input label="Degree" value={edu.degree} onChange={e => set(i, "degree", e.target.value)} fullWidth />
          <Input label="Institution" value={edu.institution} onChange={e => set(i, "institution", e.target.value)} fullWidth />
          <Input label="Year" value={edu.graduation_year} onChange={e => set(i, "graduation_year", e.target.value)} fullWidth />
          <Button variant="ghost" size="sm" onClick={() => remove(i)}><Trash2 size={13} /></Button>
        </div>
      ))}
      <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} onClick={add}>Add education</Button>
    </div>
  );
}

// ─── Skills editor ─────────────────────────────────────────────────────────
function SkillsEditor({ skills, onChange }: { skills: string[]; onChange: (v: string[]) => void }) {
  const [input, setInput] = useState("");
  const add = () => {
    const s = input.trim();
    if (s && !skills.includes(s)) { onChange([...skills, s]); setInput(""); }
  };
  return (
    <div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
        {skills.map((s, i) => (
          <span key={i} style={{ display: "flex", alignItems: "center", gap: "6px", padding: "4px 10px", borderRadius: "999px", background: "rgba(139,92,246,0.1)", color: "var(--accent-violet)", fontSize: "0.8rem" }}>
            {s}
            <button onClick={() => onChange(skills.filter((_, idx) => idx !== i))} style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", lineHeight: 1 }}>×</button>
          </span>
        ))}
      </div>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <Input value={input} onChange={e => setInput(e.target.value)} placeholder="Add a skill (e.g. React, Python)" onKeyDown={e => { if (e.key === "Enter") add(); }} fullWidth />
        <Button variant="secondary" size="sm" onClick={add}>Add</Button>
      </div>
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────
export default function ProfilePage() {
  const { addToast } = useUIStore();
  const qc = useQueryClient();
  const { data: profile, isLoading } = useQuery({ queryKey: ["profile"], queryFn: () => profileApi.get() });

  const [form, setForm] = useState<any>(null);
  const initialized = !!form;

  // Initialise form from profile on first load
  if (profile && !initialized) {
    setForm({ ...profile });
  }

  const updateMutation = useMutation({
    mutationFn: (data: any) => profileApi.update(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
      addToast({ type: "success", message: "Profile saved!" });
    },
    onError: () => addToast({ type: "error", message: "Save failed. Try again." }),
  });

  if (isLoading || !form) return (
    <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
      <Spinner size="lg" />
    </div>
  );

  const set = (key: string) => (e: any) => setForm((p: any) => ({ ...p, [key]: e.target.value }));

  return (
    <div style={{ padding: "2rem", maxWidth: "820px", margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "2rem" }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-heading)", fontSize: "1.75rem", fontWeight: 700, marginBottom: "0.25rem" }}>Profile</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Your data feeds every AI feature — CV builder, roadmap, and job matching.</p>
          </div>
          <Button variant="primary" leftIcon={<Save size={15} />} onClick={() => updateMutation.mutate(form)} loading={updateMutation.isPending}>
            Save changes
          </Button>
        </div>

        {/* Personal */}
        <Section icon={<User size={16} />} title="Personal information">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <Input label="Full name" value={form.full_name ?? ""} onChange={set("full_name")} fullWidth />
            <Input label="Email" type="email" value={form.email ?? ""} onChange={set("email")} fullWidth />
            <Input label="Phone" value={form.phone ?? ""} onChange={set("phone")} placeholder="+44 7700 000000" fullWidth />
            <Input label="Location" value={form.location ?? ""} onChange={set("location")} placeholder="London, UK" fullWidth />
            <Input label="LinkedIn URL" value={form.linkedin_url ?? ""} onChange={set("linkedin_url")} placeholder="linkedin.com/in/..." fullWidth />
            <Input label="GitHub URL" value={form.github_url ?? ""} onChange={set("github_url")} placeholder="github.com/..." fullWidth />
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <Textarea label="Professional summary" value={form.summary ?? ""} onChange={set("summary")} rows={4} fullWidth placeholder="A short, compelling overview of who you are professionally." hint="AI uses this verbatim on your CV — no hallucination." />
          </div>
        </Section>

        {/* Experience */}
        <Section icon={<Briefcase size={16} />} title="Work experience">
          <ExperienceEditor items={form.experience ?? []} onChange={v => setForm((p: any) => ({ ...p, experience: v }))} />
        </Section>

        {/* Education */}
        <Section icon={<GraduationCap size={16} />} title="Education">
          <EducationEditor items={form.education ?? []} onChange={v => setForm((p: any) => ({ ...p, education: v }))} />
        </Section>

        {/* Skills */}
        <Section icon={<Code size={16} />} title="Skills">
          <SkillsEditor skills={form.skills ?? []} onChange={v => setForm((p: any) => ({ ...p, skills: v }))} />
        </Section>

        {/* Certifications */}
        <Section icon={<Award size={16} />} title="Certifications">
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {(form.certifications ?? []).map((c: string, i: number) => (
              <div key={i} style={{ display: "flex", gap: "0.5rem" }}>
                <Input value={c} onChange={e => { const a = [...(form.certifications ?? [])]; a[i] = e.target.value; setForm((p: any) => ({ ...p, certifications: a })); }} fullWidth />
                <Button variant="ghost" size="sm" onClick={() => { const a = (form.certifications ?? []).filter((_: any, idx: number) => idx !== i); setForm((p: any) => ({ ...p, certifications: a })); }}><Trash2 size={13} /></Button>
              </div>
            ))}
            <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} onClick={() => setForm((p: any) => ({ ...p, certifications: [...(p.certifications ?? []), ""] }))}>
              Add certification
            </Button>
          </div>
        </Section>

        {/* Projects */}
        <Section icon={<Globe size={16} />} title="Projects">
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {(form.projects ?? []).map((proj: any, i: number) => (
              <div key={i} style={{ padding: "0.75rem", borderRadius: "10px", background: "var(--bg-overlay)", border: "1px solid var(--border-subtle)" }}>
                <div style={{ display: "flex", gap: "0.75rem", marginBottom: "0.5rem" }}>
                  <Input label="Project name" value={proj.name ?? ""} onChange={e => { const a = [...(form.projects ?? [])]; a[i] = { ...a[i], name: e.target.value }; setForm((p: any) => ({ ...p, projects: a })); }} fullWidth />
                  <Input label="URL" value={proj.url ?? ""} onChange={e => { const a = [...(form.projects ?? [])]; a[i] = { ...a[i], url: e.target.value }; setForm((p: any) => ({ ...p, projects: a })); }} fullWidth />
                </div>
                <Textarea label="Description" value={proj.description ?? ""} onChange={e => { const a = [...(form.projects ?? [])]; a[i] = { ...a[i], description: e.target.value }; setForm((p: any) => ({ ...p, projects: a })); }} rows={2} fullWidth />
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "0.5rem" }}>
                  <Button variant="ghost" size="sm" onClick={() => setForm((p: any) => ({ ...p, projects: (p.projects ?? []).filter((_: any, idx: number) => idx !== i) }))}><Trash2 size={13} /></Button>
                </div>
              </div>
            ))}
            <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} onClick={() => setForm((p: any) => ({ ...p, projects: [...(p.projects ?? []), { name: "", url: "", description: "" }] }))}>
              Add project
            </Button>
          </div>
        </Section>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "1.5rem" }}>
          <Button variant="primary" leftIcon={<Save size={15} />} onClick={() => updateMutation.mutate(form)} loading={updateMutation.isPending}>
            Save all changes
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
