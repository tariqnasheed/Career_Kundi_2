/**
 * CVTemplatePreview.tsx — live preview engine for 15 distinct CV layouts (CVB-F2).
 */

import type { ProfileRead } from "../../types/api";
import type { CVTemplateMeta } from "./CVTemplateGallery";

export interface PreviewPerson {
  name: string;
  headline: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
  skills: string[];
  experience: { title: string; org: string; dates: string; bullets: string[] }[];
  education: { degree: string; school: string; dates: string }[];
  projects: { title: string; blurb: string }[];
}

function buildPreviewPerson(profile?: ProfileRead | null): PreviewPerson {
  if (!profile) {
    return {
      name: "Alex Rivera",
      headline: "Product-minded engineer · systems · delivery",
      email: "alex@example.com",
      phone: "+1 555 0100",
      location: "Remote / Hybrid",
      summary:
        "Builder focused on reliable systems, clear communication, and measurable outcomes across product and engineering teams.",
      skills: ["TypeScript", "Python", "SQL", "Cloud", "APIs", "Leadership"],
      experience: [
        {
          title: "Senior Engineer",
          org: "Northwind Labs",
          dates: "2022 – Present",
          bullets: ["Shipped platform services used by 40k users", "Cut incident MTTR by 35%"],
        },
        {
          title: "Software Engineer",
          org: "Brightline",
          dates: "2019 – 2022",
          bullets: ["Owned onboarding funnel improvements", "Mentored 3 junior engineers"],
        },
      ],
      education: [{ degree: "BSc Computer Science", school: "State University", dates: "2015 – 2019" }],
      projects: [
        { title: "CareerOps Dashboard", blurb: "Analytics workspace for hiring funnels." },
        { title: "Resume Diff Tool", blurb: "ATS-safe CV comparison utility." },
      ],
    };
  }

  const skills = (profile.skills ?? []).map((s) => s.name).filter(Boolean).slice(0, 8);
  const experience = (profile.work_experiences ?? []).slice(0, 3).map((we) => ({
    title: we.job_title || "Role",
    org: we.company_name || "Organization",
    dates: [we.start_date, we.is_current ? "Present" : we.end_date].filter(Boolean).join(" – ") || "",
    bullets: (we.description_bullets ?? []).slice(0, 2),
  }));
  const education = (profile.educations ?? []).slice(0, 2).map((edu) => ({
    degree: edu.degree || "Degree",
    school: edu.institution || "Institution",
    dates: [edu.start_date, edu.end_date].filter(Boolean).join(" – ") || "",
  }));
  const projects = (profile.projects ?? []).slice(0, 3).map((p) => ({
    title: p.title || "Project",
    blurb: p.description || p.role || (p.technologies?.slice(0, 3).join(", ") ?? "Impact project"),
  }));

  return {
    name: profile.full_name || "Your Name",
    headline: profile.professional_headline || "Professional headline",
    email: profile.email || "you@email.com",
    phone: profile.phone || "",
    location: [profile.address_city, profile.address_country].filter(Boolean).join(", ") || "",
    summary: profile.bio_summary || profile.summary || "Add a professional summary in your profile to improve this preview.",
    skills: skills.length ? skills : ["Skill A", "Skill B", "Skill C"],
    experience: experience.length
      ? experience
      : [{ title: "Experience", org: "Add roles in Profile", dates: "", bullets: ["Complete your profile for richer drafts"] }],
    education: education.length
      ? education
      : [{ degree: "Education", school: "Add education in Profile", dates: "" }],
    projects: projects.length
      ? projects
      : [{ title: "Projects", blurb: "Add projects in Profile to showcase impact." }],
  };
}

function ContactLine({ person }: { person: PreviewPerson }) {
  return (
    <p className="cv-preview__contact">
      {[person.email, person.phone, person.location].filter(Boolean).join(" · ")}
    </p>
  );
}

interface CVTemplatePreviewProps {
  template: CVTemplateMeta;
  profile?: ProfileRead | null;
}

export function CVTemplatePreview({ template, profile }: CVTemplatePreviewProps) {
  const person = buildPreviewPerson(profile);
  const cls = `cv-template-preview ${template.previewClass}`;

  switch (template.id) {
    case "bold-sidebar":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <aside className="cv-preview__sidebar">
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
            <h3>Skills</h3>
            <ul>{person.skills.map((s) => <li key={s}>{s}</li>)}</ul>
          </aside>
          <div className="cv-preview__main">
            <h2>Summary</h2>
            <p>{person.summary}</p>
            <h2>Experience</h2>
            {person.experience.map((ex) => (
              <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
                <strong>{ex.title}</strong> — {ex.org}
                <div className="cv-preview__muted">{ex.dates}</div>
                <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
              </div>
            ))}
          </div>
        </article>
      );

    case "editorial-modern":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__editorial-head">
            <div>
              <p className="cv-preview__eyebrow">Curriculum Vitae</p>
              <h1>{person.name}</h1>
            </div>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__editorial-grid">
            <section>
              <h2>Narrative</h2>
              <p>{person.summary}</p>
              <h2>Selected work</h2>
              {person.experience.map((ex) => (
                <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
                  <strong>{ex.title}</strong>
                  <div className="cv-preview__muted">{ex.org} · {ex.dates}</div>
                </div>
              ))}
            </section>
            <aside>
              <h2>Capabilities</h2>
              <div className="cv-preview__chip-wrap">
                {person.skills.map((s) => <span key={s} className="cv-preview__chip">{s}</span>)}
              </div>
              <h2>Projects</h2>
              {person.projects.map((p) => (
                <div key={p.title} className="cv-preview__block">
                  <strong>{p.title}</strong>
                  <p>{p.blurb}</p>
                </div>
              ))}
            </aside>
          </div>
        </article>
      );

    case "technical-matrix":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Skill matrix</h2>
          <div className="cv-preview__matrix">
            {person.skills.map((s) => <div key={s} className="cv-preview__matrix-cell">{s}</div>)}
          </div>
          <h2>Systems & projects</h2>
          <div className="cv-preview__project-grid">
            {person.projects.map((p) => (
              <div key={p.title} className="cv-preview__project-card">
                <strong>{p.title}</strong>
                <p>{p.blurb}</p>
              </div>
            ))}
          </div>
          <h2>Experience</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> @ {ex.org}
              <div className="cv-preview__muted">{ex.dates}</div>
            </div>
          ))}
        </article>
      );

    case "executive-classic":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__exec-head">
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Executive summary</h2>
          <p>{person.summary}</p>
          <h2>Leadership & impact</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block cv-preview__block--gold">
              <strong>{ex.title}</strong>
              <div className="cv-preview__muted">{ex.org} · {ex.dates}</div>
              <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          ))}
        </article>
      );

    case "graduate-starter":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Education</h2>
          {person.education.map((ed) => (
            <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
              <strong>{ed.degree}</strong>
              <div className="cv-preview__muted">{ed.school} · {ed.dates}</div>
            </div>
          ))}
          <h2>Projects</h2>
          {person.projects.map((p) => (
            <div key={p.title} className="cv-preview__block">
              <strong>{p.title}</strong>
              <p>{p.blurb}</p>
            </div>
          ))}
          <h2>Skills</h2>
          <p>{person.skills.join(" · ")}</p>
          <h2>Experience</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
            </div>
          ))}
        </article>
      );

    case "project-portfolio":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Featured projects</h2>
          <div className="cv-preview__project-grid">
            {person.projects.map((p) => (
              <div key={p.title} className="cv-preview__project-card">
                <strong>{p.title}</strong>
                <p>{p.blurb}</p>
              </div>
            ))}
          </div>
          <h2>Background</h2>
          <p>{person.summary}</p>
          <h2>Experience</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
            </div>
          ))}
        </article>
      );

    case "data-analyst-grid":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__metrics">
            <div className="cv-preview__metric"><span>Insights</span><strong>40+</strong></div>
            <div className="cv-preview__metric"><span>Dashboards</span><strong>12</strong></div>
            <div className="cv-preview__metric"><span>Tools</span><strong>{Math.max(person.skills.length, 6)}</strong></div>
          </div>
          <h2>Tools grid</h2>
          <div className="cv-preview__matrix">
            {person.skills.map((s) => <div key={s} className="cv-preview__matrix-cell">{s}</div>)}
          </div>
          <h2>Analytics work</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
              <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          ))}
        </article>
      );

    case "creative-professional":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <div className="cv-preview__creative-banner">
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
          </div>
          <ContactLine person={person} />
          <div className="cv-preview__creative-cols">
            <section>
              <h2>About</h2>
              <p>{person.summary}</p>
              <h2>Experience</h2>
              {person.experience.map((ex) => (
                <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
                  <strong>{ex.title}</strong>
                  <div className="cv-preview__muted">{ex.org}</div>
                </div>
              ))}
            </section>
            <aside>
              <h2>Craft</h2>
              <div className="cv-preview__chip-wrap">
                {person.skills.map((s) => <span key={s} className="cv-preview__chip">{s}</span>)}
              </div>
            </aside>
          </div>
        </article>
      );

    case "academic-research":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__academic-head">
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Research interests</h2>
          <p>{person.summary}</p>
          <h2>Education</h2>
          {person.education.map((ed) => (
            <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
              <strong>{ed.degree}</strong>
              <div className="cv-preview__muted">{ed.school} · {ed.dates}</div>
            </div>
          ))}
          <h2>Selected projects / publications</h2>
          {person.projects.map((p) => (
            <div key={p.title} className="cv-preview__block">
              <strong>{p.title}</strong>
              <p>{p.blurb}</p>
            </div>
          ))}
        </article>
      );

    case "healthcare-clinical":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__credential-bar">Credentials · Licenses · Compliance-ready</div>
          <h2>Clinical / professional summary</h2>
          <p>{person.summary}</p>
          <h2>Experience</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
              <div className="cv-preview__muted">{ex.dates}</div>
            </div>
          ))}
          <h2>Education & training</h2>
          {person.education.map((ed) => (
            <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
              <strong>{ed.degree}</strong> · {ed.school}
            </div>
          ))}
        </article>
      );

    case "engineering-blueprint":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__blueprint-head">
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <h2>Engineering projects</h2>
          <div className="cv-preview__project-grid">
            {person.projects.map((p) => (
              <div key={p.title} className="cv-preview__project-card">
                <strong>{p.title}</strong>
                <p>{p.blurb}</p>
              </div>
            ))}
          </div>
          <h2>Tools & standards</h2>
          <p>{person.skills.join(" · ")}</p>
          <h2>Experience</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
            </div>
          ))}
        </article>
      );

    case "sales-achievement":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header>
            <h1>{person.name}</h1>
            <p>{person.headline}</p>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__metrics cv-preview__metrics--sales">
            <div className="cv-preview__metric"><span>Pipeline</span><strong>$2.4M</strong></div>
            <div className="cv-preview__metric"><span>Win rate</span><strong>38%</strong></div>
            <div className="cv-preview__metric"><span>Quota</span><strong>112%</strong></div>
          </div>
          <h2>Commercial impact</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong> — {ex.org}
              <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          ))}
        </article>
      );

    case "government-ats":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <h1>{person.name}</h1>
          <p>{person.headline}</p>
          <ContactLine person={person} />
          <hr />
          <h2>PROFESSIONAL SUMMARY</h2>
          <p>{person.summary}</p>
          <h2>EXPERIENCE</h2>
          {person.experience.map((ex) => (
            <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
              <strong>{ex.title}</strong>, {ex.org} ({ex.dates})
              <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          ))}
          <h2>EDUCATION</h2>
          {person.education.map((ed) => (
            <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
              {ed.degree}, {ed.school} ({ed.dates})
            </div>
          ))}
          <h2>SKILLS</h2>
          <p>{person.skills.join(", ")}</p>
        </article>
      );

    case "international-modern":
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__intl-head">
            <div>
              <h1>{person.name}</h1>
              <p>{person.headline}</p>
            </div>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__intl-grid">
            <section>
              <h2>Profile</h2>
              <p>{person.summary}</p>
              <h2>Experience</h2>
              {person.experience.map((ex) => (
                <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
                  <strong>{ex.title}</strong>
                  <div className="cv-preview__muted">{ex.org} · {ex.dates}</div>
                </div>
              ))}
            </section>
            <aside>
              <h2>Skills</h2>
              <ul>{person.skills.map((s) => <li key={s}>{s}</li>)}</ul>
              <h2>Education</h2>
              {person.education.map((ed) => (
                <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
                  <strong>{ed.degree}</strong>
                  <div className="cv-preview__muted">{ed.school}</div>
                </div>
              ))}
            </aside>
          </div>
        </article>
      );

    case "minimal-corporate":
    default:
      return (
        <article className={cls} aria-label={`${template.name} preview`}>
          <header className="cv-preview__corp-head">
            <div>
              <h1>{person.name}</h1>
              <p>{person.headline}</p>
            </div>
            <ContactLine person={person} />
          </header>
          <div className="cv-preview__corp-grid">
            <section>
              <h2>Summary</h2>
              <p>{person.summary}</p>
              <h2>Experience</h2>
              {person.experience.map((ex) => (
                <div key={`${ex.title}-${ex.org}`} className="cv-preview__block">
                  <strong>{ex.title}</strong> — {ex.org}
                  <div className="cv-preview__muted">{ex.dates}</div>
                  <ul>{ex.bullets.map((b) => <li key={b}>{b}</li>)}</ul>
                </div>
              ))}
            </section>
            <aside>
              <h2>Skills</h2>
              <ul>{person.skills.map((s) => <li key={s}>{s}</li>)}</ul>
              <h2>Education</h2>
              {person.education.map((ed) => (
                <div key={`${ed.degree}-${ed.school}`} className="cv-preview__block">
                  <strong>{ed.degree}</strong>
                  <div className="cv-preview__muted">{ed.school}</div>
                </div>
              ))}
            </aside>
          </div>
        </article>
      );
  }
}
