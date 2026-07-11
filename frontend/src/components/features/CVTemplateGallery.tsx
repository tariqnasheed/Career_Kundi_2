/**
 * CVTemplateGallery.tsx — 15-template catalog + gallery UI (CVB-F2).
 */

import { clsx } from "clsx";

export type CVTemplateId =
  | "minimal-corporate"
  | "bold-sidebar"
  | "editorial-modern"
  | "technical-matrix"
  | "executive-classic"
  | "graduate-starter"
  | "project-portfolio"
  | "data-analyst-grid"
  | "creative-professional"
  | "academic-research"
  | "healthcare-clinical"
  | "engineering-blueprint"
  | "sales-achievement"
  | "government-ats"
  | "international-modern";

export type BackendTemplateId = "modern" | "classic" | "compact" | "creative";

export interface CVTemplateMeta {
  id: CVTemplateId;
  name: string;
  category: string;
  bestFor: string;
  layoutStyle: string;
  atsLevel: "Very High" | "High" | "Medium";
  accent: string;
  accentHex: string;
  description: string;
  strengths: string[];
  previewClass: string;
  backendTemplate: BackendTemplateId;
}

export const CV_TEMPLATE_CATALOG: CVTemplateMeta[] = [
  {
    id: "minimal-corporate",
    name: "Minimal Corporate",
    category: "Professional",
    bestFor: "Engineering, business, finance, operations, formal roles",
    layoutStyle: "Clean two-column recruiter-friendly layout",
    atsLevel: "High",
    accent: "Navy",
    accentHex: "#1e3a5f",
    description: "A clean, readable, corporate CV for formal applications.",
    strengths: ["ATS-friendly", "Readable", "Formal", "Recruiter-safe"],
    previewClass: "cv-template-preview--minimal-corporate",
    backendTemplate: "classic",
  },
  {
    id: "bold-sidebar",
    name: "Bold Sidebar",
    category: "Modern",
    bestFor: "Product, marketing, operations, tech, mid-career profiles",
    layoutStyle: "Strong left sidebar with bold section hierarchy",
    atsLevel: "Medium",
    accent: "Purple / Navy",
    accentHex: "#6d28d9",
    description: "A confident layout with a strong sidebar and visual hierarchy.",
    strengths: ["Strong identity", "Skill-forward", "Modern", "Memorable"],
    previewClass: "cv-template-preview--bold-sidebar",
    backendTemplate: "creative",
  },
  {
    id: "editorial-modern",
    name: "Editorial Modern",
    category: "Design-forward",
    bestFor: "Strategy, creative-tech, leadership, portfolio-style profiles",
    layoutStyle: "Asymmetric editorial layout with premium typography",
    atsLevel: "Medium",
    accent: "Charcoal / Warm neutral",
    accentHex: "#3f3a36",
    description: "A premium editorial CV with distinctive layout and typography.",
    strengths: ["Premium", "Distinct", "Portfolio-friendly", "High visual hierarchy"],
    previewClass: "cv-template-preview--editorial-modern",
    backendTemplate: "creative",
  },
  {
    id: "technical-matrix",
    name: "Technical Matrix",
    category: "Technical",
    bestFor: "Software, cybersecurity, data, cloud, DevOps, AI roles",
    layoutStyle: "Skill matrix, project grid, technical stack emphasis",
    atsLevel: "High",
    accent: "Cyan / Slate",
    accentHex: "#0891b2",
    description: "A technical CV emphasizing tools, systems, projects, and measurable impact.",
    strengths: ["Technical clarity", "Project-heavy", "Skills matrix", "ATS-conscious"],
    previewClass: "cv-template-preview--technical-matrix",
    backendTemplate: "modern",
  },
  {
    id: "executive-classic",
    name: "Executive Classic",
    category: "Leadership",
    bestFor: "Managers, directors, senior professionals, consultants",
    layoutStyle: "Elegant executive layout with achievement-led sections",
    atsLevel: "High",
    accent: "Black / Gold",
    accentHex: "#b45309",
    description: "A mature executive CV focused on leadership, outcomes, and credibility.",
    strengths: ["Leadership", "Premium", "Formal", "Achievement-led"],
    previewClass: "cv-template-preview--executive-classic",
    backendTemplate: "classic",
  },
  {
    id: "graduate-starter",
    name: "Graduate Starter",
    category: "Early career",
    bestFor: "Fresh graduates, students, internships, entry-level jobs",
    layoutStyle: "Education-first layout with projects and skills emphasis",
    atsLevel: "High",
    accent: "Blue / Green",
    accentHex: "#059669",
    description: "A friendly early-career CV that highlights education, projects, and potential.",
    strengths: ["Beginner-friendly", "Education-first", "Project-focused", "Clean"],
    previewClass: "cv-template-preview--graduate-starter",
    backendTemplate: "compact",
  },
  {
    id: "project-portfolio",
    name: "Project Portfolio",
    category: "Portfolio",
    bestFor: "Developers, designers, engineers, freelancers, builders",
    layoutStyle: "Project cards and portfolio-style case highlights",
    atsLevel: "Medium",
    accent: "Indigo / Teal",
    accentHex: "#4f46e5",
    description: "A portfolio-style CV for candidates whose projects prove their ability.",
    strengths: ["Project-led", "Visual", "Builder-focused", "Impact-oriented"],
    previewClass: "cv-template-preview--project-portfolio",
    backendTemplate: "modern",
  },
  {
    id: "data-analyst-grid",
    name: "Data Analyst Grid",
    category: "Data",
    bestFor: "Data analysts, BI analysts, ML beginners, analytics roles",
    layoutStyle: "Metric cards, tools grid, dashboard-inspired sections",
    atsLevel: "High",
    accent: "Emerald / Slate",
    accentHex: "#047857",
    description: "A structured analytics CV with metrics, tools, and data projects clearly visible.",
    strengths: ["Metric-heavy", "Tools-focused", "Analytical", "Structured"],
    previewClass: "cv-template-preview--data-analyst-grid",
    backendTemplate: "modern",
  },
  {
    id: "creative-professional",
    name: "Creative Professional",
    category: "Creative",
    bestFor: "Design, content, marketing, media, branding roles",
    layoutStyle: "Expressive modern layout with creative section balance",
    atsLevel: "Medium",
    accent: "Pink / Violet",
    accentHex: "#db2777",
    description: "A creative CV with personality while staying professional.",
    strengths: ["Expressive", "Modern", "Creative", "Personal brand"],
    previewClass: "cv-template-preview--creative-professional",
    backendTemplate: "creative",
  },
  {
    id: "academic-research",
    name: "Academic Research",
    category: "Academic",
    bestFor: "Masters, PhD, research, teaching, publications",
    layoutStyle: "Research-focused layout with publications and academic sections",
    atsLevel: "High",
    accent: "Maroon / Navy",
    accentHex: "#7f1d1d",
    description: "A formal academic CV for research, education, and higher-study applications.",
    strengths: ["Research-ready", "Publication-friendly", "Formal", "Detailed"],
    previewClass: "cv-template-preview--academic-research",
    backendTemplate: "classic",
  },
  {
    id: "healthcare-clinical",
    name: "Healthcare Clinical",
    category: "Healthcare",
    bestFor: "Clinical, pharmacy, nursing, healthcare administration roles",
    layoutStyle: "License, clinical experience, compliance, and patient-care emphasis",
    atsLevel: "High",
    accent: "Teal / Blue",
    accentHex: "#0f766e",
    description: "A healthcare-focused CV with clinical credibility and compliance sections.",
    strengths: ["Clinical", "Compliance-aware", "Credential-focused", "Clear"],
    previewClass: "cv-template-preview--healthcare-clinical",
    backendTemplate: "classic",
  },
  {
    id: "engineering-blueprint",
    name: "Engineering Blueprint",
    category: "Engineering",
    bestFor: "Electrical, mechanical, civil, MEP, site, design engineers",
    layoutStyle: "Blueprint-inspired layout with projects, tools, and standards",
    atsLevel: "High",
    accent: "Blueprint Blue",
    accentHex: "#1d4ed8",
    description: "An engineering CV focused on projects, calculations, standards, and tools.",
    strengths: ["Engineering-focused", "Project-heavy", "Standards-aware", "Technical"],
    previewClass: "cv-template-preview--engineering-blueprint",
    backendTemplate: "modern",
  },
  {
    id: "sales-achievement",
    name: "Sales Achievement",
    category: "Sales",
    bestFor: "Sales, business development, account management, customer success",
    layoutStyle: "Revenue, targets, pipeline, and achievement-forward sections",
    atsLevel: "High",
    accent: "Orange / Navy",
    accentHex: "#ea580c",
    description: "A commercial CV focused on numbers, deals, targets, and growth.",
    strengths: ["Achievement-led", "Metric-focused", "Commercial", "Outcome-driven"],
    previewClass: "cv-template-preview--sales-achievement",
    backendTemplate: "classic",
  },
  {
    id: "government-ats",
    name: "Government ATS",
    category: "Public sector",
    bestFor: "Government, public sector, compliance-heavy applications",
    layoutStyle: "Plain, structured, conservative ATS-first format",
    atsLevel: "Very High",
    accent: "Gray / Navy",
    accentHex: "#334155",
    description: "A conservative ATS-safe CV for public-sector and formal applications.",
    strengths: ["ATS-first", "Formal", "Clear", "Compliance-friendly"],
    previewClass: "cv-template-preview--government-ats",
    backendTemplate: "compact",
  },
  {
    id: "international-modern",
    name: "International Modern",
    category: "Global",
    bestFor: "UK, EU, GCC, Canada, Australia, international applications",
    layoutStyle: "Global professional layout with balanced profile and experience sections",
    atsLevel: "High",
    accent: "Royal Blue / Charcoal",
    accentHex: "#1e40af",
    description: "A globally professional CV style suitable for international job applications.",
    strengths: ["Global-ready", "Balanced", "Professional", "Modern"],
    previewClass: "cv-template-preview--international-modern",
    backendTemplate: "modern",
  },
];

export function getCVTemplate(id: CVTemplateId): CVTemplateMeta {
  return CV_TEMPLATE_CATALOG.find((t) => t.id === id) ?? CV_TEMPLATE_CATALOG[0];
}

interface CVTemplateGalleryProps {
  selectedId: CVTemplateId;
  onSelect: (id: CVTemplateId) => void;
}

export function CVTemplateGallery({ selectedId, onSelect }: CVTemplateGalleryProps) {
  return (
    <section className="cv-template-gallery" aria-label="CV template gallery">
      <header className="cv-template-gallery__header">
        <h2>Template gallery</h2>
        <p>{CV_TEMPLATE_CATALOG.length} structurally distinct layouts — select to update live preview</p>
      </header>
      <div className="cv-template-gallery__grid">
        {CV_TEMPLATE_CATALOG.map((tpl) => {
          const active = tpl.id === selectedId;
          return (
            <button
              key={tpl.id}
              type="button"
              className={clsx("cv-template-card", active && "cv-template-card--active")}
              onClick={() => onSelect(tpl.id)}
              aria-pressed={active}
            >
              <div className="cv-template-card__thumb" style={{ ["--tpl-accent" as string]: tpl.accentHex }}>
                <span className={`cv-template-card__mini cv-template-card__mini--${tpl.id}`} />
              </div>
              <div className="cv-template-card__body">
                <div className="cv-template-card__title-row">
                  <strong>{tpl.name}</strong>
                  <span className="cv-template-card__ats">{tpl.atsLevel} ATS</span>
                </div>
                <span className="cv-template-card__category">{tpl.category}</span>
                <p>{tpl.layoutStyle}</p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
