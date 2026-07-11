# CareerKundi Master Build Plan

**Document type:** Permanent product + engineering operating manual  
**Companion file:** [`docs/product/careerkundi_live_tracker.md`](careerkundi_live_tracker.md)  
**Last architecture update:** 2026-07-11 (UX0-S1)  
**Repo fact rule:** Use `VERIFY_IN_REPO` when a path, hash, endpoint, or test is not verified.

---

## 1. Executive Summary

CareerKundi is a modern AI-powered career, learning, evidence, roadmap, preparation, and opportunity operating system. It helps people understand who they are, what they have done, what they want next, and how to prepare and apply safely.

UI must be planned before more feature work because navigation, page ownership, and user journeys determine which backend modules and APIs are safe to build. Backend and frontend must be linked by domains so every feature has one owner on each side. AI must be governed because LLM output can invent facts, leak context, or take unsafe actions.

This master build plan is the permanent operating manual for architecture, ladder, templates, and anti-drift rules. The separate live tracker is the short GPS file for current slice status.

**Hard rule:** No major feature should be implemented unless it has a defined navigation location, backend owner, frontend owner, API/data contract, permission model, UI states, test journey, evidence file, and commit boundary.

---

## 2. Two-File Operating Model

| File | Role | Update frequency |
|---|---|---|
| `docs/product/careerkundi_master_build_plan.md` | Full architecture and technical operating manual | Only when architecture, ladder, slice cards, major decisions, templates, or product direction change |
| `docs/product/careerkundi_live_tracker.md` | Current GPS: position, next slice, blockers, evidence, commits | Every future CareerKundi slice |

**Rules:**

- Master Build Plan = full architecture and technical operating manual.
- Live Tracker = current GPS position of the project.
- The live tracker is updated every slice.
- The master plan is updated only when the plan changes.
- Future Cursor prompts must read both files before acting.
- No slice is closed unless the live tracker is updated.
- Neither file may contain secrets, tokens, credentials, or raw sensitive user data.
- The live tracker must stay short and operational (readable in under 2 minutes).
- Architecture details belong in the master build plan, not the tracker.

---

## 3. Research-Backed Engineering Principles

### React UI architecture
**Source:** React official documentation — Thinking in React  
Break UI into a component hierarchy; map UI structure to data model shape; build static UI before complex interactivity; keep state minimal; avoid duplicated derived state; place state at the closest correct owner.

### React Router architecture
**Source:** React Router official documentation — Routing  
Use a planned route hierarchy; use an authenticated layout shell; use nested/layout routes where useful; routes must match product concepts; navigation groups must be predictable.

### Vite build discipline
**Source:** Vite official documentation — Building for Production  
`frontend/dist` is generated build output and must stay ignored/untracked.

### FastAPI modular backend
**Source:** FastAPI official documentation — Bigger Applications  
Use modular packages for large backend areas; use route modules / APIRouter-style organization; keep models, schemas, services, routes, tests, and docs together per domain.

### Accessibility
**Source:** W3C WCAG 2.2  
Perceivable, operable, understandable, robust; keyboard navigation; visible focus states; input labels; clear errors; contrast; responsive layout.

### API security
**Sources:** OWASP API Security Top 10 2023; OWASP Authorization Cheat Sheet  
Every user-owned object route needs object-level authorization; never trust user-controlled IDs; deny by default; authorization must be checked server-side.

### LLM / GenAI security
**Source:** OWASP Top 10 for LLM Applications  
Protect against prompt injection and sensitive information disclosure; avoid excessive agency; validate model outputs before use; avoid misinformation; control cost and unbounded consumption; protect tool use.

### AI risk governance
**Source:** NIST AI Risk Management Framework  
Govern, map, measure, manage; require human review for high-impact actions.

### Agentic AI architecture
**Source:** Anthropic — Building Effective Agents  
Start with simple deterministic workflows; use structured LLM calls before autonomous agents; use agents only where flexible reasoning and tool use are truly needed; add human checkpoints for high-impact actions.

### Gemini function calling
**Source:** Google Gemini API documentation — Function Calling  
Prefer structured tool/function calling for model-to-tool workflows instead of loose prose.

### MCP later
**Source:** Model Context Protocol documentation  
MCP may later help connect external tools and data sources, but do not introduce it before core CareerKundi workflows are stable.

---

## 4. CareerKundi Product North Star

CareerKundi is:

> A modern AI-powered career, learning, evidence, roadmap, preparation, and opportunity operating system.

It is **not merely** a CV builder, job search app, chatbot, roadmap page, or interview question generator.

**Core product loop:**

1. Who are you?
2. What have you done?
3. What claims do you make?
4. What evidence supports them?
5. What do you want next?
6. Which pathways are available?
7. What are your gaps?
8. What should you learn?
9. What should you practice?
10. What proof should you create?
11. Which opportunities fit?
12. How should you prepare?
13. How should you apply safely?
14. What happened?
15. What should change next?

---

## 5. Current Accepted Technical State

| Item | Status | Verified commit / note |
|---|---|---|
| 0050 Platform Foundation | Completed and pushed | `29a27493` — `feat(platform): add 0050 foundation architecture` |
| CP4-B frontend/dist cleanup | Completed and pushed | `6c1ac4fe` — `chore(frontend): stop tracking Vite build output` |
| 004E frozen work | Archived locally; active tree cleaned | Desktop archive — VERIFY_IN_REPO for exact archive path |
| Report/artifact cleanup | Archived locally; active tree cleaned | Desktop archive — VERIFY_IN_REPO for exact archive path |
| PF11 Platform Foundation Shell | Committed and pushed | `3b8827ec` — `feat(frontend): add platform foundation shell` |

**Verified existing authenticated routes (App.tsx):** `/dashboard`, `/jobs`, `/interview-pack` (redirect), `/cv-builder`, `/roadmap`, `/achievements`, `/profile`, `/settings`, `/platform`, `/chatbot`.

**Verified platform backend packages:** `kernel`, `identity`, `provenance`, `claims`, `geo`, `lifecycle`, `privacy`, `observability`.

**Frozen directions:**

- Old 004E Interview Pack repair is **not** the active product direction.
- Future **Interview Studio** is a new system.
- Old Auto Apply is **not** the active product direction.
- Future **Safe Apply** is a new system.

---

## 6. Decision Log

| Date | Decision | Reason | Impact | Status |
|---|---|---|---|---|
| 2026-07 | 0050 Platform Foundation is closed | Foundation APIs and DB lineage verified | New features build on platform kernel | Accepted |
| 2026-07 | `frontend/dist` remains ignored/untracked | Vite build output must not pollute Git | CP4-B hygiene | Accepted |
| 2026-07 | Old 004E repair is frozen | Drift and repair cost too high | Interview Studio replaces it | Accepted |
| 2026-07 | Future Interview Studio is a new system | Clean architecture vs patching 004E | New ladder items 0061+ | Accepted |
| 2026-07 | Old Auto Apply is frozen | Unsafe agency risk | Safe Apply replaces it | Accepted |
| 2026-07 | Future Safe Apply is a new system | Human review gates required | New ladder item 0068 | Accepted |
| 2026-07 | PF11 belongs under Career Core → Platform | Foundation shell is career-core, not a side tool | Nav placement | Accepted |
| 2026-07 | Roadmaps are platform-wide, not only Graduate Launch | Roadmaps serve all personas | ROAD-* before 0056 | Accepted |
| 2026-07 | CV Builder and Roadmaps stabilized before 0051 | Visible product value before taxonomy depth | CVB-* / ROAD-* next after UX0 | Accepted |
| 2026-07-11 | Master build plan and live tracker are separate files | Avoid mixing architecture with GPS | Two-file operating model | Accepted |
| 2026-07-11 | Live tracker must be updated with every future slice | Prevent status drift | Slice close rule | Accepted |

---

## 7. User Personas and Core Journeys

### Personas

| Persona | Main goal | Pain points | Most important pages | Backend domains | Success moment | MVP | Future |
|---|---|---|---|---|---|---|---|
| Student / fresh graduate | First role + CV + roadmap | No experience narrative | Dashboard, CV, Roadmaps, Graduate Launch | passport, cv, roadmaps | First CV + roadmap | High | Deep launch navigator |
| Early-career job seeker | Jobs + interview prep | Scattered tools | Jobs, Interview Studio, Applications | opportunities, interview, applications | Saved job + prep pack | High | Fit intelligence |
| Career switcher | New pathway + gap plan | Unclear transferable skills | Passport, Skills, Roadmaps | passport, skills, roadmaps | Switch plan with gaps | Medium | Role trials |
| Skilled migrant candidate | Mobility + eligibility | Jurisdiction confusion | Migration, Education, Opportunities | mobility, geo, education | Clear pathway checklist | Low MVP | Full mobility engine |
| Study abroad candidate | Programs + language | Source freshness | Study Abroad, Language Exams | education, mobility | Shortlist + requirements | Low MVP | Source engine |
| Public-sector candidate | Exams + deadlines | Unreliable sources | Public Sector, Prep | public_sector | Deadline-aware plan | Low MVP | Exam prep engine |
| Experienced professional | Evidence + targeted apply | Generic AI output | Passport, Claims, CV, Applications | claims, cv, applications | Evidence-backed CV | Medium | Outcome learning |
| Admin / B2B partner (future) | Cohort tooling | Not built | Admin (future) | b2b | Cohort dashboard | Deferred | 0076 |

### Core journeys

| Journey | Entry | Steps | Backend | Frontend | AI level | Human review | Success | MVP | Future |
|---|---|---|---|---|---|---|---|---|---|
| Create career passport | `/passport` | Profile → education → experience → skills | passport, claims | passport pages | L0–L1 | Claims verification | Passport complete | After 0052 | Evidence graph |
| Build CV | `/cv-builder` | Template → edit → preview → export | cv_builder | cv-builder | L1 drafts | Export | PDF exported | CVB-F* | AI rewrite |
| Generate roadmap | `/roadmaps` | Goal → generate/create → tasks | roadmaps, lifecycle | roadmaps | L1–L2 | Accept plan | Roadmap saved | ROAD-F* | Taxonomy 0051 |
| Find opportunity | `/jobs/search` | Search → save → fit | opportunities | jobs | L1 fit | None for save | Job saved | Existing `/jobs` | 0054–0055 |
| Prepare interview | `/interview-studio` | Session → practice → study | interview_studio | interview-studio | L1–L2 | Pack quality | Session complete | After 0061 | Full studio |
| Create evidence/proof | `/proof` | Claim → source → proof | claims, provenance | proof | L0–L1 | Verification | Proof linked | After 0053 | 0060 |
| Apply safely | `/applications/safe-apply` | Draft → review → submit | applications | applications | L1 draft | **Required** | Submitted after review | After 0068 | Automation assist |
| Track outcome | `/applications/tracker` | Status → outcome | applications, lifecycle | applications | L0 | None | Outcome logged | Later | 0062 |
| Improve next cycle | Dashboard | Insights → next actions | observability + domains | dashboard | L1 | None | Next action taken | Later | Outcome learning |

---

## 8. Product Scope Levels

| Level | Meaning |
|---|---|
| 0 | Not planned in current slice |
| 1 | Route placeholder / information page |
| 2 | Read-only MVP |
| 3 | Create/edit MVP |
| 4 | AI-assisted workflow |
| 5 | Integrated workflow with evidence/provenance |
| 6 | Production-ready with analytics, permissions, and release gate |

Use these levels in all feature tables.

---

## 9. Public Website Information Architecture

| Page | Purpose | Main sections | Primary CTA | Secondary CTA | Do not overclaim | MVP | Future |
|---|---|---|---|---|---|---|---|
| `/` | Landing | Brand, value, how it works, trust | Register | Login | Do not claim unfinished engines complete | Existing | Motion polish |
| Features | Product overview | Feature cards by domain | Start free | See pricing | Label preview vs ready | Planned | Deep demos |
| Pricing | Plans | Free vs paid | Start free | Contact | No fake enterprise claims | Deferred | 0075 |
| About | Mission | Story, principles | Register | Help | Honest scope | Planned | Team |
| Help | Support | FAQs, contact | Open help | Login | No fake live chat | Planned | Knowledge base |
| Login | Auth | Email/password | Sign in | Register | — | Existing | SSO later |
| Register | Auth | Create account | Create account | Login | — | Existing | Email verify UX |

**Landing message:** CareerKundi helps users build a career profile, create CVs, generate roadmaps, prepare interviews, find opportunities, and track applications.

---

## 10. Authenticated App Shell Architecture

**Zones:** left sidebar; topbar; breadcrumb; command/search (later); notifications (later); user menu; main content; right contextual assistant panel (later); responsive mobile nav; toast/status; modal/drawer.

**Behavior:** active route highlight; collapsible sidebar; mobile drawer; page title + breadcrumb; global search later; command palette later; assistant panel contextual to current page.

**Current verified shell:** `AppShell` + `Sidebar` + `Header` + toast container + chatbot FAB (`VERIFY_IN_REPO` for exact CSS modules).

---

## 11. Final Navigation Map

### Home
**Why:** Orientation and next actions.  
**Backend:** aggregates. **Immediate:** `/dashboard`. **Future:** `/today`, `/progress`. **MVP:** Dashboard shell. **Not built:** Today/Progress depth.

### Career Core
**Why:** Identity, subjects, claims, skills.  
**Backend:** platform, passport, claims, skills. **Immediate:** `/platform`, `/profile`. **Future:** `/passport/*`, `/skills`, Claims & Evidence. **MVP:** Platform shell (PF11). **Not built:** full passport/claims UI.

### Build
**Why:** Artifacts employers see.  
**Backend:** cv_builder. **Immediate:** `/cv-builder`. **Future:** templates/editor/preview/export, cover letters, portfolio, documents. **MVP:** CVB-F*. **Not built:** cover letters/portfolio.

### Roadmaps
**Why:** Platform-wide pathway engine (not Graduate-only).  
**Backend:** roadmaps, lifecycle. **Immediate:** `/roadmap` (existing singular). **Future:** `/roadmaps/*` family. **MVP:** ROAD-F*. **Not built:** specialized plan types.

### Opportunities
**Why:** Find and evaluate roles.  
**Backend:** opportunities / job_search. **Immediate:** `/jobs`. **Future:** saved, match, company research, public/remote. **MVP:** existing jobs surface. **Not built:** full opportunity intelligence.

### Prepare
**Why:** Interview and practice.  
**Backend:** interview_studio, skills. **Immediate:** legacy interview-pack redirect only. **Future:** Interview Studio, study, practice, role trials, mocks. **MVP:** after 0061. **Not built:** Studio.

### Education & Mobility
**Why:** Study abroad, exams, migration. **MVP:** Level 1 placeholders later. **Not built:** engines.

### Applications
**Why:** Safe apply + tracking. **MVP:** tracker later. **Not built:** Safe Apply (0068). **Frozen:** old Auto Apply.

### Account
**Why:** Settings/privacy/billing/help. **Immediate:** `/settings`. **Future:** privacy, billing, help. **Not built:** billing.

---

## 12. Route Hierarchy Table

| Route | Page name | Nav group | Access | Backend domain | Frontend owner | Current status | MVP priority | Notes |
|---|---|---|---|---|---|---|---|---|
| `/` | Landing | Public | Public | — | pages/LandingPage | Existing | High | |
| `/login` | Login | Public | Public | auth | pages/LoginPage | Existing | High | |
| `/register` | Register | Public | Public | auth | pages/RegisterPage | Existing | High | |
| `/dashboard` | Dashboard | Home | Auth | aggregate | pages/DashboardPage | Existing shell | High | Needs blueprint rebuild |
| `/platform` | Platform Foundation | Career Core | Auth | platform | pages/PlatformPage | Existing (PF11) | High | Subjects + goals |
| `/passport` | Career Passport | Career Core | Auth | career_passport | features/passport | Planned | Medium | After 0052 |
| `/passport/profile` | Passport Profile | Career Core | Auth | career_passport | features/passport | Planned | Medium | |
| `/passport/education` | Education | Career Core | Auth | career_passport | features/passport | Planned | Medium | |
| `/passport/experience` | Experience | Career Core | Auth | career_passport | features/passport | Planned | Medium | |
| `/passport/projects` | Projects | Career Core | Auth | career_passport | features/passport | Planned | Medium | |
| `/passport/skills` | Skills | Career Core | Auth | career_passport / skills | features/passport | Planned | Medium | |
| `/passport/targets` | Targets | Career Core | Auth | lifecycle | features/passport | Planned | Medium | |
| `/cv-builder` | CV Builder | Build | Auth | cv_builder | pages/CVBuilderPage | Existing | High | Stabilize CVB-F* |
| `/cv-builder/templates` | Templates | Build | Auth | cv_builder | features/cv-builder | Planned | High | CVB-F2 |
| `/cv-builder/editor` | Editor | Build | Auth | cv_builder | features/cv-builder | Planned | High | |
| `/cv-builder/preview` | Preview | Build | Auth | cv_builder | features/cv-builder | Planned | High | |
| `/cv-builder/export` | Export | Build | Auth | cv_builder | features/cv-builder | Planned | High | Human review on export |
| `/roadmap` | Roadmap (legacy path) | Roadmaps | Auth | roadmaps | pages/RoadmapPage | Existing | High | Map to `/roadmaps` later |
| `/roadmaps` | My Roadmaps | Roadmaps | Auth | roadmaps | features/roadmaps | Planned | High | ROAD-F* |
| `/roadmaps/new` | Generate/Create | Roadmaps | Auth | roadmaps | features/roadmaps | Planned | High | |
| `/roadmaps/:id` | Roadmap detail | Roadmaps | Auth | roadmaps | features/roadmaps | Planned | High | |
| `/roadmaps/:id/tasks` | Tasks | Roadmaps | Auth | roadmaps | features/roadmaps | Planned | High | |
| `/opportunities` | Opportunities hub | Opportunities | Auth | opportunities | features/opportunities | Planned | Medium | |
| `/jobs/search` | Job search | Opportunities | Auth | job_search / opportunities | jobs | Planned alias | High | Today `/jobs` |
| `/jobs/saved` | Saved jobs | Opportunities | Auth | job_search | jobs | Partial in `/jobs` | High | VERIFY_IN_REPO |
| `/jobs/:id` | Job detail | Opportunities | Auth | job_search | jobs | Partial | High | |
| `/interview-studio` | Interview Studio | Prepare | Auth | interview_studio | features/interview-studio | Planned | Medium | New system |
| `/interview-studio/practice` | Practice | Prepare | Auth | interview_studio | features/interview-studio | Planned | Medium | |
| `/skills` | Skills | Career Core | Auth | skills | features/skills | Planned | Medium | |
| `/practice` | Practice tasks | Prepare | Auth | skills | features/skills | Planned | Medium | |
| `/proof` | Proof artifacts | Prepare | Auth | claims / skills | features/skills | Planned | Medium | After 0053/0060 |
| `/graduate-launch` | Graduate Launch | Roadmaps/Launch | Auth | graduate_launch | features/education | Planned | Low | After 0056 |
| `/public-sector` | Public sector | Education & Mobility | Auth | public_sector | features/public-sector | Planned | Low | |
| `/education` | Education hub | Education & Mobility | Auth | education | features/education | Planned | Low | |
| `/study-abroad` | Study abroad | Education & Mobility | Auth | education | features/education | Planned | Low | |
| `/masters-phd` | Masters/PhD | Education & Mobility | Auth | education | features/education | Planned | Low | |
| `/migration` | Migration | Education & Mobility | Auth | mobility | features/education | Planned | Low | |
| `/applications` | Applications hub | Applications | Auth | applications | features/applications | Planned | Medium | |
| `/applications/tracker` | Tracker | Applications | Auth | applications | features/applications | Planned | Medium | |
| `/applications/drafts` | Drafts | Applications | Auth | applications | features/applications | Planned | Medium | |
| `/applications/safe-apply` | Safe Apply | Applications | Auth | applications | features/applications | Planned | Low | After 0068 |
| `/settings` | Settings | Account | Auth | profile/auth | pages/SettingsPage | Existing | High | |
| `/privacy` | Privacy | Account | Auth | privacy | features/settings | Planned | Medium | |
| `/billing` | Billing | Account | Auth | billing | features/settings | Deferred | Low | After 0075 |
| `/achievements` | Achievements | Community (current) | Auth | badges | pages/AchievementsPage | Existing | Low | Re-home later |
| `/chatbot` | Chatbot | Assistant | Auth | chatbot | pages/ChatbotPage | Existing | Medium | Evolve to assistant panel |
| `/profile` | Profile | Career Core | Auth | profile | pages/ProfilePage | Existing | Medium | Merge toward passport |

---

## UX0-S2 Navigation + Sitemap Contract

**Slice:** UX0-S2  
**Date:** 2026-07-11  
**Type:** Docs-only contract (no product route/sidebar implementation in this slice)  
**Inspected files (read-only):** `frontend/src/App.tsx`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/Header.tsx`, `frontend/src/main.tsx`, `frontend/src/pages/*`

### 6.1 Current Route Inventory

Verified from `App.tsx` route table + page imports. Status values: `EXISTING_VERIFIED` | `EXISTING_NEEDS_REVIEW` | `PLANNED` | `PLACEHOLDER_NEEDED` | `DEFERRED` | `FROZEN` | `VERIFY_IN_REPO`.

| Route | Page / Component | Access | Current Status | Source File | Notes |
|---|---|---|---|---|---|
| `/` | `LandingPage` | Public (`PublicRoute`) | EXISTING_VERIFIED | `pages/LandingPage.tsx` via `App.tsx` | Logged-in users redirected to `/dashboard` |
| `/login` | `LoginPage` | Public (`PublicRoute`) | EXISTING_VERIFIED | `pages/LoginPage.tsx` | |
| `/register` | `RegisterPage` | Public (`PublicRoute`) | EXISTING_VERIFIED | `pages/RegisterPage.tsx` | |
| `/dashboard` | `DashboardPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/DashboardPage.tsx` | Sidebar: Dashboard |
| `/jobs` | `JobSearchPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/JobSearchPage.tsx` | Sidebar label: Jobs & Interview Prep; not yet `/jobs/search` |
| `/interview-pack` | `InterviewPackRedirect` → `/jobs` | Auth + `AppShell` | FROZEN | `App.tsx` redirect | Legacy URL; **do not repair 004E pack**. `InterviewPackPage.tsx` file exists but is **not** mounted |
| `/cv-builder` | `CVBuilderPage` | Auth + `AppShell` | EXISTING_NEEDS_REVIEW | `pages/CVBuilderPage.tsx` | Single route today; nested templates/editor/preview/export are PLANNED |
| `/roadmap` | `RoadmapPage` | Auth + `AppShell` | EXISTING_NEEDS_REVIEW | `pages/RoadmapPage.tsx` | Singular path; future contract prefers `/roadmaps` |
| `/achievements` | `AchievementsPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/AchievementsPage.tsx` | Sidebar Community group; re-home later |
| `/profile` | `ProfilePage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/ProfilePage.tsx` | Merge toward `/passport` later |
| `/settings` | `SettingsPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/SettingsPage.tsx` | |
| `/platform` | `PlatformPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/PlatformPage.tsx` | PF11; Sidebar Career Tools → Platform; breadcrumb Platform Foundation |
| `/chatbot` | `ChatbotPage` | Auth + `AppShell` | EXISTING_VERIFIED | `pages/ChatbotPage.tsx` | Route exists; **not** in Sidebar `NAV_GROUPS` (FAB/widget only) |
| `*` | `NotFoundPage` | Any | EXISTING_VERIFIED | `pages/NotFoundPage.tsx` | Catch-all |

**Current sidebar groups (verified `Sidebar.tsx`):** Main (Dashboard, Jobs); Career Tools (CV Builder, Career Roadmap, Platform); Community (Achievements); Account (Profile, Settings).

**Current breadcrumb labels (verified `Header.tsx` `PAGE_LABELS`):** dashboard, jobs, cv-builder, roadmap, achievements, profile, settings, platform. Missing explicit labels for `chatbot`, `interview-pack` → fall back to segment title-case (`VERIFY_IN_REPO` for runtime).

### 6.2 Planned Route Contract

| Planned Route | Page Name | Navigation Group | Access | Backend Domain | Frontend Owner | MVP Priority | Implementation Slice | Status |
|---|---|---|---|---|---|---|---|---|
| `/` | Landing | Public | Public | — | pages/LandingPage | High | Existing | EXISTING_VERIFIED |
| `/login` | Login | Public | Public | auth | pages/LoginPage | High | Existing | EXISTING_VERIFIED |
| `/register` | Register | Public | Public | auth | pages/RegisterPage | High | Existing | EXISTING_VERIFIED |
| `/dashboard` | Dashboard | Home | Auth | aggregate | pages/DashboardPage | High | UX0-S5+ shell polish | EXISTING_VERIFIED |
| `/platform` | Platform Foundation | Career Core | Auth | platform | pages/PlatformPage | High | PF11 done; PF11-R1 review | EXISTING_VERIFIED |
| `/passport` | Career Passport | Career Core | Auth | career_passport | features/passport | Medium | After 0052 | PLANNED |
| `/passport/profile` | Passport Profile | Career Core | Auth | career_passport | features/passport | Medium | After 0052 | PLANNED |
| `/passport/education` | Education | Career Core | Auth | career_passport | features/passport | Medium | After 0052 | PLANNED |
| `/passport/experience` | Experience | Career Core | Auth | career_passport | features/passport | Medium | After 0052 | PLANNED |
| `/passport/projects` | Projects | Career Core | Auth | career_passport | features/passport | Medium | After 0052 | PLANNED |
| `/passport/skills` | Skills | Career Core | Auth | career_passport / skills | features/passport | Medium | After 0052 | PLANNED |
| `/passport/targets` | Targets | Career Core | Auth | lifecycle | features/passport | Medium | After 0052 | PLANNED |
| `/cv-builder` | CV Builder | Build | Auth | cv_builder | pages/CVBuilderPage | High | CVB-F0–F5 | EXISTING_NEEDS_REVIEW |
| `/cv-builder/templates` | Templates | Build | Auth | cv_builder | features/cv-builder | High | CVB-F2 | PLANNED |
| `/cv-builder/editor` | Editor | Build | Auth | cv_builder | features/cv-builder | High | CVB-F1/F2 | PLANNED |
| `/cv-builder/preview` | Preview | Build | Auth | cv_builder | features/cv-builder | High | CVB-F2 | PLANNED |
| `/cv-builder/export` | Export | Build | Auth | cv_builder | features/cv-builder | High | CVB-F3 | PLANNED |
| `/roadmaps` | My Roadmaps | Roadmaps | Auth | roadmaps | features/roadmaps | High | ROAD-F1+ | PLANNED |
| `/roadmap` | Career Roadmap (legacy) | Roadmaps | Auth | roadmaps | pages/RoadmapPage | High | ROAD-F0/F1; alias later | EXISTING_NEEDS_REVIEW |
| `/roadmaps/new` | Generate/Create Roadmap | Roadmaps | Auth | roadmaps | features/roadmaps | High | ROAD-F2 | PLANNED |
| `/roadmaps/:id` | Roadmap Detail | Roadmaps | Auth | roadmaps | features/roadmaps | High | ROAD-F3 | PLANNED |
| `/roadmaps/:id/tasks` | Roadmap Tasks | Roadmaps | Auth | roadmaps | features/roadmaps | High | ROAD-F3 | PLANNED |
| `/opportunities` | Opportunities Hub | Opportunities | Auth | opportunities | features/opportunities | Medium | After 0054–55 | PLANNED |
| `/jobs/search` | Job Search | Opportunities | Auth | job_search | jobs | High | Alias of `/jobs` later | PLANNED |
| `/jobs` | Jobs & Interview Prep | Opportunities | Auth | job_search | pages/JobSearchPage | High | Existing surface | EXISTING_VERIFIED |
| `/jobs/saved` | Saved Jobs | Opportunities | Auth | job_search | jobs | High | VERIFY_IN_REPO (may be panel inside `/jobs`) | PLANNED / VERIFY_IN_REPO |
| `/jobs/:id` | Job Detail | Opportunities | Auth | job_search | jobs | High | VERIFY_IN_REPO | PLANNED / VERIFY_IN_REPO |
| `/interview-studio` | Interview Studio | Prepare | Auth | interview_studio | features/interview-studio | Medium | After 0061 | PLANNED |
| `/interview-studio/practice` | Practice | Prepare | Auth | interview_studio | features/interview-studio | Medium | After 0061 | PLANNED |
| `/interview-pack` | Legacy redirect | Prepare | Auth | — | App redirect | Low | Keep redirect only | FROZEN |
| `/skills` | Skills | Career Core | Auth | skills | features/skills | Medium | After 0060 | PLANNED |
| `/practice` | Practice Tasks | Prepare | Auth | skills | features/skills | Medium | After 0060 | PLANNED |
| `/proof` | Proof Artifacts | Prepare | Auth | claims / skills | features/skills | Medium | After 0053/0060 | PLANNED |
| `/graduate-launch` | Graduate Launch | Roadmaps / Launch | Auth | graduate_launch | features/education | Low | After 0056 | PLANNED |
| `/public-sector` | Public Sector | Education & Mobility | Auth | public_sector | features/public-sector | Low | After 0063+ | PLANNED |
| `/education` | Education Hub | Education & Mobility | Auth | education | features/education | Low | After 0069+ | PLANNED |
| `/study-abroad` | Study Abroad | Education & Mobility | Auth | education | features/education | Low | After 0070 | PLANNED |
| `/masters-phd` | Masters / PhD | Education & Mobility | Auth | education | features/education | Low | After 0072 | PLANNED |
| `/migration` | Migration | Education & Mobility | Auth | mobility | features/education | Low | After 0073 | PLANNED |
| `/applications` | Applications Hub | Applications | Auth | applications | features/applications | Medium | After 0068 prep | PLANNED |
| `/applications/tracker` | Application Tracker | Applications | Auth | applications | features/applications | Medium | Later | PLANNED |
| `/applications/drafts` | Drafts | Applications | Auth | applications | features/applications | Medium | Later | PLANNED |
| `/applications/safe-apply` | Safe Apply | Applications | Auth | applications | features/applications | Low | After 0068 | PLANNED |
| `/settings` | Settings | Account | Auth | profile/auth | pages/SettingsPage | High | Existing | EXISTING_VERIFIED |
| `/privacy` | Privacy | Account | Auth | privacy | features/settings | Medium | Later | PLANNED |
| `/billing` | Billing | Account | Auth | billing | features/settings | Low | After 0075 | DEFERRED |
| `/achievements` | Achievements | Account / Community | Auth | badges | pages/AchievementsPage | Low | Existing; re-home later | EXISTING_VERIFIED |
| `/chatbot` | Chatbot | Assistant | Auth | chatbot | pages/ChatbotPage | Medium | Evolve to panel | EXISTING_VERIFIED |
| `/profile` | Profile | Career Core | Auth | profile | pages/ProfilePage | Medium | Merge toward passport | EXISTING_VERIFIED |

### 6.3 Sidebar Navigation Contract

Target grouped sidebar (future implementation slices only — **not** implemented in UX0-S2):

| Group | Display label | Primary routes (now / first MVP) | Future routes | First MVP page | Icon category | Backend domain | Visibility |
|---|---|---|---|---|---|---|---|
| Home | Home | `/dashboard` | `/today`, `/progress` | `/dashboard` | layout / home | aggregate | AUTHENTICATED |
| Career Core | Career Core | `/platform`, `/profile` | `/passport/*`, Claims & Evidence, `/skills` | `/platform` | identity / layers | platform, passport, claims, skills | AUTHENTICATED |
| Build | Build | `/cv-builder` | `/cv-builder/templates|editor|preview|export`, cover letters, portfolio, documents | `/cv-builder` | document / book | cv_builder | AUTHENTICATED |
| Roadmaps | Roadmaps | `/roadmap` (legacy) → `/roadmaps` | `/roadmaps/new`, `/:id`, `/:id/tasks`, specialized plans | `/roadmap` then `/roadmaps` | map / path | roadmaps, lifecycle | AUTHENTICATED |
| Opportunities | Opportunities | `/jobs` | `/jobs/search`, `/jobs/saved`, `/jobs/:id`, `/opportunities`, company research, remote/public | `/jobs` | search / briefcase | job_search, opportunities | AUTHENTICATED |
| Prepare | Prepare | (none in sidebar yet; legacy pack frozen) | `/interview-studio`, practice, study, role trials, mocks | `/interview-studio` after 0061 | target / mic | interview_studio, skills | FUTURE_FEATURE |
| Education & Mobility | Education & Mobility | (none) | `/education`, `/study-abroad`, `/masters-phd`, `/migration`, `/public-sector`, `/graduate-launch` | Level-1 placeholders later | globe / graduation | education, mobility, public_sector | FUTURE_FEATURE |
| Applications | Applications | (none) | `/applications`, tracker, drafts, `/applications/safe-apply` | tracker later; Safe Apply after 0068 | send / inbox | applications | FUTURE_FEATURE (Safe Apply not Auto Apply) |
| Account | Account | `/settings`, `/profile`, `/achievements` | `/privacy`, `/billing`, Help | `/settings` | user / gear | profile, privacy, billing | AUTHENTICATED; billing = BILLING_GATED_FUTURE |

**Visibility values used:** `PUBLIC` | `AUTHENTICATED` | `FUTURE_FEATURE` | `ADMIN_FUTURE` | `BILLING_GATED_FUTURE`.

**Current vs target:** Today’s sidebar still uses Main / Career Tools / Community / Account. Remapping to the contract above requires an explicit frontend nav slice **after** UX0-S2 and UX0-S3 — not in this slice.

### 6.4 Breadcrumb Contract

| Route | Breadcrumb Label | Parent | Notes |
|---|---|---|---|
| `/dashboard` | Dashboard | Home | Verified `PAGE_LABELS.dashboard` |
| `/platform` | Platform Foundation | Career Core | Verified `PAGE_LABELS.platform` |
| `/profile` | Profile | Career Core | Verified |
| `/cv-builder` | CV Builder | Build | Verified |
| `/cv-builder/templates` | Templates | CV Builder | PLANNED |
| `/cv-builder/editor` | Editor | CV Builder | PLANNED |
| `/cv-builder/preview` | Preview | CV Builder | PLANNED |
| `/cv-builder/export` | Export | CV Builder | PLANNED |
| `/roadmap` | Career Roadmap | Roadmaps | Verified `PAGE_LABELS.roadmap` |
| `/roadmaps` | Roadmaps | Roadmaps | PLANNED (plural) |
| `/roadmaps/new` | New Roadmap | Roadmaps | PLANNED |
| `/roadmaps/:id` | Roadmap Detail | Roadmaps | PLANNED |
| `/jobs` | Jobs & Interview Prep | Opportunities | Verified |
| `/jobs/search` | Job Search | Opportunities | PLANNED |
| `/jobs/saved` | Saved Jobs | Opportunities | PLANNED |
| `/passport` | Career Passport | Career Core | PLANNED |
| `/interview-studio` | Interview Studio | Prepare | PLANNED |
| `/applications` | Applications | Applications | PLANNED |
| `/applications/safe-apply` | Safe Apply | Applications | PLANNED; never “Auto Apply” |
| `/settings` | Settings | Account | Verified |
| `/privacy` | Privacy | Account | PLANNED |
| `/billing` | Billing | Account | DEFERRED |
| `/chatbot` | Chatbot (fallback) | Assistant | No `PAGE_LABELS` entry today — VERIFY_IN_REPO runtime fallback |
| `/achievements` | Achievements | Account / Community | Verified |

### 6.5 Access Contract

| Route Group | Access Rule | Auth Behavior | Unauthorized Behavior | Notes |
|---|---|---|---|---|
| Public (`/`, `/login`, `/register`) | PUBLIC | `PublicRoute`: if already authenticated → `/dashboard` | N/A (public) | Verified in `App.tsx` |
| Authenticated app (AppShell children) | AUTHENTICATED | `PrivateRoute` + `useAuthStore().isAuthenticated`; spinner while `isLoading` | Navigate to `/login` | No auth bypass allowed |
| Catch-all `*` | Any | Renders `NotFoundPage` | — | Exists outside PrivateRoute |
| Admin / B2B future | ADMIN_FUTURE | Deferred | Deferred | No routes yet |
| Billing-gated future | BILLING_GATED_FUTURE | Deferred | Deferred | `/billing` DEFERRED |
| Frozen legacy pack | FROZEN | `/interview-pack` redirects to `/jobs` | Same as auth routes | Do not revive 004E |
| Frozen Auto Apply | FROZEN | No route | — | Future is Safe Apply only |

### 6.6 UX0-S2 Implementation Decision

UX0-S2 is a **docs-only** sitemap/navigation contract.

- No product route implementation is included in this slice.
- No sidebar product-code changes are included in this slice.
- Future route/sidebar implementation must happen through **explicit frontend slices after UX0-S2 and UX0-S3**.
- Do not invent EXISTING status for planned routes.
- Frozen: old 004E Interview Pack repair; old Auto Apply.

---

## 13. Dashboard Blueprint

| Section | Purpose | Data | Backend source | Empty state | Primary action | Secondary | MVP | Future | Analytics | Tech notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Career Snapshot | Who/where | Subject, goals, profile completeness | platform + profile | Create subject / complete profile | Open Platform | Open Passport | Shell | Deep passport | `passport_completed` | Aggregate read APIs |
| Next Best Actions | Guidance | Ranked actions | deterministic rules first | Show onboarding checklist | Do top action | Dismiss | Shell | AI ranking L1 | action_clicked | No agent yet |
| Active Roadmaps | Progress | Roadmap list | roadmaps | Create roadmap | Open roadmap | New roadmap | After ROAD-F1 | AI generate | `roadmap_created` | |
| Opportunity Feed | Jobs | Saved/recent | job_search | Search jobs | Open jobs | Save job | Existing jobs link | Fit scores | `job_saved` | |
| Preparation Hub | Prep | Sessions | interview_studio | Start practice | Interview Studio | Study | Placeholder | Studio | `interview_session_started` | |
| Application Tracker | Pipeline | Applications | applications | Create draft | Tracker | Safe Apply | Placeholder | Full tracker | `application_draft_created` | |
| AI Career Assistant | Help | Context of page | assistant | Ask a question | Open assistant | Tips | Existing chatbot | Contextual panel | assistant_opened | Level 1 first |

**Dashboard states:** new user; returning user; active roadmap; applications present; interview prep active.

---

## 14. Page Blueprint Standard

Every page must define:

- route, navigation group, page purpose, primary user goal
- primary action, secondary actions
- backend data source, API endpoints, components used
- loading / empty / error / unauthorized / success states
- mobile behavior, analytics events, browser journey test
- what not to build yet, allowed files, forbidden files, commit boundary

This standard is mandatory for future implementation prompts.

---

## 15. Immediate Page Blueprints

### `/platform`
- **Layout:** Title + foundation status + subjects list + goals panel.
- **API:** `GET/POST /api/v1/platform/subjects`, `GET/POST /api/v1/platform/subjects/{id}/goals` (verified PF8/PF11).
- **States:** loading/empty/error for subjects and goals; auth via PrivateRoute.
- **MVP scope:** subjects + goals only. **Not yet:** claims, privacy, geo, lifecycle UI.
- **Browser journey:** login → `/platform` → create subject → create goal → refresh persist.
- **Risks:** overclaiming foundation completeness.

### `/dashboard`
- **Layout:** snapshot + next actions + cards linking to CV/Roadmap/Jobs/Platform.
- **MVP:** honest shell with links; no fake analytics. **Future:** live aggregates.
- **Browser journey:** login → dashboard loads without console errors.

### `/cv-builder` (+ templates/editor/preview/export)
- **Layout:** section forms + template gallery + preview frame + export CTA.
- **MVP:** load, edit, template, preview, save/load, PDF export (CVB-F0–F5).
- **Not yet:** advanced AI rewrite agents.
- **Human review:** export.
- **Browser journey:** template → edit → preview → save → refresh → load → export.

### `/roadmaps` (+ new/:id/tasks)
- **Layout:** list/empty → create → detail timeline → tasks.
- **MVP:** ROAD-F0–F3. Platform-wide (not Graduate-only).
- **Not yet:** full AI roadmap engine / taxonomy intelligence (needs 0051).
- **Browser journey:** create → open detail → complete task → refresh persist.

---

## 16. Design System and Visual Direction

**Style:** modern, premium, clean, trustworthy, career-focused, slightly futuristic, accessible, mobile-responsive.

**Tokens (define in UX0-S3):** colors; typography scale; spacing; radius; elevation; surface levels; status colors; focus rings; restrained motion.

**Status categories:** success, warning, danger, info, neutral, draft, verified, unverified, blocked, in progress, complete.

**Core components:** Button, Card, Badge, Tabs, Dialog, Drawer, Toast, Command palette, Sidebar, Breadcrumb, Input, Select, Textarea, Date picker, Progress, Timeline, Stepper, Data table, Skeleton, Empty/Error states, Evidence card, Roadmap milestone card, Opportunity card, CV preview frame, Assistant panel.

| Category | Purpose | Where used | A11y | Priority | Notes |
|---|---|---|---|---|---|
| Button/Input | Actions/forms | All | Labels, focus | Existing | Extend, don't rewrite |
| Card/Badge | Surfaces/status | Lists | Contrast | Existing | |
| Dialog/Drawer | Overlays | Confirm/export | Focus trap | Medium | |
| Timeline/Stepper | Roadmaps | Roadmaps | Keyboard | High for ROAD | |
| Evidence card | Claims | Passport/proof | Clear status | Later | |
| CV preview | Preview | CV Builder | Readable | High for CVB | |
| Assistant panel | Context help | Shell | Esc/close | Later | |

---

## 17. Component Inventory by Feature

| Feature | Page | Required | Shared | Feature-specific | MVP | Future |
|---|---|---|---|---|---|---|
| Platform | `/platform` | List, forms, toast | Button, Card, Input, Spinner | Subject card, Goal form | Present | Claims UI later |
| Dashboard | `/dashboard` | Cards, CTAs | Card, Button | Snapshot, Next actions | Shell | Live widgets |
| CV Builder | `/cv-builder*` | Forms, preview, export | Input, Button, Modal | Template gallery, Preview frame | Audit→repair | AI assist |
| Roadmaps | `/roadmaps*` | List, timeline | Card, Progress | Milestone, Task row | Audit→repair | AI generate |
| Career Passport | `/passport*` | Sections | Form controls | Passport section nav | Planned | Evidence |
| Opportunities | `/jobs*` | Search, cards | Card, Badge | Job card, filters | Partial existing | Fit analysis |
| Interview Studio | `/interview-studio*` | Session UI | Tabs, Card | Question panel, Study panel | Planned | Full studio |
| Applications | `/applications*` | Tracker table | Table, Badge | Draft editor, review gate | Planned | Safe Apply |
| Education/Mobility | hubs | Info pages | Card | Requirement checklist | Level 1 later | Engines |
| Settings | `/settings` | Forms | Input, Toggle | Privacy panels | Partial | Billing |

---

## 18. Feature Product Map

| Feature | Purpose | Routes | Backend | Frontend | APIs | Models | UI states | Security | Analytics | Future | Not yet | First slice |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Platform Foundation | Subjects/goals shell | `/platform` | `app/platform` | PlatformPage | platform subjects/goals | career_subjects, career_goals | L/E/E | Owner checks | subject/goal created | Claims UI | Claims/privacy UI | PF11 done; PF11-R1 |
| Career Passport | Career identity | `/passport*` | career_passport | features/passport | planned | profile records | L/E/E | Owner | passport_completed | Evidence | Deep claims | After 0052 |
| CV Builder | CV create/export | `/cv-builder*` | cv_builder | cv-builder | existing+planned | CV versions | L/E/E | Owner; export review | cv_* | AI rewrite | Agents | CVB-F0 |
| Roadmaps | Pathway plans | `/roadmaps*` | roadmaps | roadmaps | existing+planned | roadmaps/tasks | L/E/E | Owner | roadmap_* | Taxonomy | Graduate-only ownership | ROAD-F0 |
| Opportunity Intelligence | Fit + sources | `/opportunities`, `/jobs*` | opportunities | opportunities | planned | jobs/fit | L/E/E | Owner | job_* | 0054–55 | Fake certainty | After UX0 + jobs honesty |
| Interview Studio | Prep system | `/interview-studio*` | interview_studio | interview-studio | planned | sessions | L/E/E | Owner | interview_* | Full studio | 004E repair | After 0061 |
| Skills→Practice→Proof | Capability loop | `/skills`,`/practice`,`/proof` | skills/claims | skills | planned | skills/proof | L/E/E | Owner+provenance | practice_* | Badges | Unverified claims | After 0060 |
| Graduate Launch | Grad navigator | `/graduate-launch` | graduate_launch | education | planned | launch plans | L/E/E | Owner | — | Deep | Before 0056 | After 0056 |
| Public Sector | Gov careers | `/public-sector` | public_sector | public-sector | planned | exams | L/E/E | Source freshness | — | Exam prep | Fake deadlines | After 0063+ |
| Study Abroad / Education | Education paths | `/education*` | education | education | planned | programs | L/E/E | Source rules | — | Engines | Unsourced advice | After 0069+ |
| Applications / Safe Apply | Apply safely | `/applications*` | applications | applications | planned | drafts/submissions | L/E/E | **Human review** | application_* | Assist | Blind auto-apply | After 0068 |
| Settings / Privacy / Billing | Account | `/settings`,`/privacy`,`/billing` | privacy/billing | settings | partial | prefs/subs | L/E/E | Privacy | — | Billing | Early billing | Privacy before billing |
| Notifications | Alerts | shell | notifications | layout | planned | notifications | — | Privacy | — | Channels | Spam | Later |
| AI Career Assistant | Contextual help | panel/chatbot | agent_orchestration | assistant | partial chatbot | context | — | No sensitive logs | assistant_* | Tools | Autonomous agents | Evolve chatbot |
| Admin / B2B | Partners | future | b2b | admin | planned | orgs | — | RBAC | — | 0076 | Now | Deferred |

---

## 19. Backend Architecture

**Existing (verified):** `backend/app/platform/` → kernel, identity, provenance, claims, geo, lifecycle, privacy, observability.

**Future modules:**

```text
backend/app/career_passport/
backend/app/cv_builder/
backend/app/roadmaps/
backend/app/opportunities/
backend/app/interview_studio/
backend/app/skills/
backend/app/applications/
backend/app/education/
backend/app/public_sector/
backend/app/mobility/
backend/app/billing/
backend/app/notifications/
backend/app/agent_orchestration/
```

Each module should have: `models.py`, `schemas.py`, `service.py`, `routes.py`, `tests/`, `README.md`.

**Rules:** No random cross-module DB access; use service contracts; every route checks ownership; every LLM output has validation; every high-impact generated artifact preserves provenance.

---

## 20. Backend Module Build Template

For every future backend module define:

- module purpose; owned tables; read/write dependencies
- Pydantic schemas; service functions; route endpoints
- auth/ownership checks; privacy classification; provenance requirements
- migration needed?; tests required; runtime smoke check

---

## 21. Data Contract Matrix

| Feature | Frontend route | Frontend folder | Backend module | Primary models | Primary APIs | Auth/ownership | Provenance | Privacy | Status | MVP slice |
|---|---|---|---|---|---|---|---|---|---|---|
| Platform | `/platform` | pages/PlatformPage | platform | subjects, goals | `/api/v1/platform/*` | User owns subject | Goal create actor | User data | Existing | PF11 |
| Passport | `/passport*` | features/passport | career_passport | profile records | planned | Owner | Claims later | High | Planned | 0052 |
| CV | `/cv-builder*` | cv-builder | cv_builder | CV versions | planned/existing | Owner | Export lineage | High | Partial | CVB-F* |
| Roadmaps | `/roadmaps*` | roadmaps | roadmaps | roadmaps, tasks | planned/existing | Owner | Optional | Medium | Partial | ROAD-F* |
| Jobs | `/jobs*` | JobSearchPage | job_search | saved_jobs | existing | Owner | Sources | Medium | Existing | honesty already |
| Interview Studio | `/interview-studio*` | interview-studio | interview_studio | sessions | planned | Owner | Sources | Medium | Planned | 0061 |
| Applications | `/applications*` | applications | applications | drafts, submissions | planned | Owner + review | Required | High | Planned | 0068 |
| Education | `/education*` | education | education | plans | planned | Owner | Source freshness | High | Planned | 0069+ |
| Billing | `/billing` | settings | billing | subscriptions | planned | Owner | Audit | High | Deferred | 0075 |
| Assistant | chatbot/panel | chatbot | agent_orchestration | context | partial | Owner | Redact logs | High | Partial | evolve |

---

## 22. API Endpoint Planning Matrix

| Feature | Endpoint | Method | Purpose | Request | Response | Owner check | Privacy/provenance | MVP status |
|---|---|---|---|---|---|---|---|---|
| platform | `/api/v1/platform/subjects` | GET | List subjects | — | `{data, meta}` | Auth user | — | **existing** |
| platform | `/api/v1/platform/subjects` | POST | Create subject | empty | `{data}` | Auth user | — | **existing** |
| platform | `/api/v1/platform/subjects/{id}` | GET | Get subject | — | `{data}` | Owned | — | **existing** |
| platform | `/api/v1/platform/subjects/{id}/goals` | GET | List goals | — | `{data, meta}` | Owned | — | **existing** |
| platform | `/api/v1/platform/subjects/{id}/goals` | POST | Create goal | GoalCreate | `{data}` | Owned | actor provenance | **existing** |
| passport | `/api/v1/passport/*` | * | Passport CRUD | planned | planned | Owned | High | **planned MVP** |
| cv | `/api/v1/cv-builder/versions` | GET/POST | Versions | planned | planned | Owned | Export lineage | **planned MVP** |
| cv | `/api/v1/cv-builder/versions/{id}` | GET/PATCH | Version | planned | planned | Owned | — | **planned MVP** |
| roadmaps | `/api/v1/roadmaps` | GET/POST | List/create | planned | planned | Owned | — | **planned MVP** |
| roadmaps | `/api/v1/roadmaps/{id}` | GET/PATCH | Detail | planned | planned | Owned | — | **planned MVP** |
| roadmaps | `/api/v1/roadmaps/{id}/tasks` | POST | Add task | planned | planned | Owned | — | **planned MVP** |
| roadmaps | `/api/v1/roadmaps/{id}/tasks/{task_id}` | PATCH | Update task | planned | planned | Owned | — | **planned MVP** |
| opportunities | `/api/v1/opportunities/*` | * | Fit/intelligence | planned | planned | Owned | Source notes | **future** |
| interview | `/api/v1/interview-studio/*` | * | Sessions | planned | planned | Owned | Sources | **future** |
| skills/proof | `/api/v1/skills/*` `/proof/*` | * | Practice/proof | planned | planned | Owned | Provenance | **future** |
| applications | `/api/v1/applications/*` | * | Drafts/submit | planned | planned | Owned + review | High | **future** |
| education | `/api/v1/education/*` | * | Plans | planned | planned | Owned | Source freshness | **deferred** |
| notifications | `/api/v1/notifications/*` | * | Alerts | planned | planned | Owned | No sensitive body logs | **deferred** |
| billing | `/api/v1/billing/*` | * | Subs | planned | planned | Owned | Audit | **deferred** |
| assistant | `/api/v1/chatbot/*` or assistant | * | Chat | existing/partial | existing | Owned | Redaction | **existing/partial** |

Do not pretend planned endpoints already exist.

---

## 23. Database / Model Planning Matrix

| Domain | Model/Table | Purpose | Module | Reads | Writes | Privacy | Provenance | MVP |
|---|---|---|---|---|---|---|---|---|
| platform | career_subjects | Career subject | identity | user | user | High | — | Existing |
| platform | career_goals | Goals | lifecycle | subject | subject | High | actor | Existing |
| passport | passport profile | Identity | career_passport | subject | subject | High | optional | Planned |
| passport | education records | Education | career_passport | subject | subject | High | optional | Planned |
| passport | experience records | Work history | career_passport | subject | subject | High | optional | Planned |
| passport | projects | Projects | career_passport | subject | subject | Medium | optional | Planned |
| skills | skills | Skill inventory | skills | subject | subject | Medium | optional | Planned |
| claims | career_claims | Claims | claims | subject | subject | High | Required | Foundation exists; UI later |
| provenance | sources/snapshots | Evidence | provenance | claim | claim | High | Required | Foundation exists |
| cv | CV versions | CV docs | cv_builder | user/subject | user | High | Export | Planned |
| cv | CV templates | Template meta | cv_builder | all | admin | Low | — | Planned |
| roadmaps | roadmaps | Plans | roadmaps | subject | subject | Medium | optional | Partial existing |
| roadmaps | milestones/tasks | Progress | roadmaps | roadmap | roadmap | Medium | — | Planned |
| jobs | saved_jobs | Saved jobs | job_search | user | user | Medium | source_url | Existing |
| opportunities | fit analyses | Fit | opportunities | user | system | Medium | sources | Future |
| interview | sessions | Prep | interview_studio | user | user | Medium | sources | Future |
| study | study modules | Study | interview_studio | session | system | Medium | sources | Future |
| practice | practice tasks | Practice | skills | user | user | Medium | — | Future |
| proof | proof artifacts | Proof | skills/claims | user | user | High | Required | Future |
| applications | drafts | Drafts | applications | user | user | High | — | Future |
| applications | submissions | Submissions | applications | user | user+review | High | Required | Future |
| applications | outcomes | Outcomes | applications | user | user | Medium | — | Future |
| billing | subscriptions | Plans | billing | user | billing | High | Audit | Deferred |
| notifications | notifications | Alerts | notifications | user | system | Medium | No raw secrets | Deferred |
| assistant | assistant context | Context | agent_orchestration | user | user | High | Redact | Partial |

---

## 24. Frontend Architecture

Recommended future structure:

```text
frontend/src/
  app/ routes.tsx providers.tsx layout/
  components/ ui/ layout/ career/ cv/ roadmap/ opportunity/ interview/
  features/ platform/ passport/ cv-builder/ roadmaps/ opportunities/
           interview-studio/ skills/ applications/ education/ public-sector/
  lib/ api.ts auth.ts dates.ts errors.ts
  types/ api.ts platform.ts passport.ts cv.ts roadmap.ts opportunity.ts
  pages/
```

**State:** Move toward this incrementally. Do **not** do a giant frontend rewrite just to match the folder map.

---

## 25. Frontend Feature Build Template

Define for every frontend feature: route; page component; feature folder; shared + feature-specific components; API client methods; types; state categories; loading/empty/error/success; auth/unauthorized; mobile; browser journey; console expectations; `frontend/dist` ignored check.

---

## 26. Frontend State and Data-Fetching Rules

| Category | Examples | Rule |
|---|---|---|
| Server data | subjects, goals, CVs | Shared API/query layer |
| Form state | goal title, CV fields | Local / form-library owned |
| UI-only state | sidebar collapsed, modal open | UI store |
| Auth/session | tokens, user | Auth store; no duplication |
| Assistant context | page context | Explicit, redacted |

Derived values must not be duplicated in state. API errors use shared error display. Every page needs loading/empty/error/unauthorized states.

---

## 27. Security / Privacy / Permission Matrix

| Resource | Owner | Read | Write | Auth check | Privacy | Consent/retention | High-impact? | Human review? |
|---|---|---|---|---|---|---|---|---|
| career subject | user | owner | owner | ensure_owned_subject | High | Account retention | No | No |
| career passport | user | owner | owner | ownership | High | User export/delete | No | Claims verify later |
| claim | user | owner | owner | ownership | High | Evidence retention | Yes if verified | Yes to verify |
| source/snapshot | user | owner | system/user | ownership | High | Retention policy | No | Source QA |
| CV | user | owner | owner | ownership | High | User delete | Export yes | Export review |
| roadmap | user | owner | owner | ownership | Medium | — | No | Accept AI plan |
| saved job | user | owner | owner | ownership | Medium | — | No | No |
| interview session | user | owner | owner | ownership | Medium | — | No | Pack quality |
| application draft | user | owner | owner | ownership | High | — | No | Before submit |
| application submission | user | owner | owner+gate | ownership + review gate | High | Audit | **Yes** | **Required** |
| education/migration plan | user | owner | owner | ownership | High | Jurisdiction rules | Yes | Source review |
| billing/subscription | user | owner | billing svc | ownership | High | Legal retention | Yes | Ops |
| notification | user | owner | system | ownership | Medium | Opt-in | No | No |
| assistant context | user | owner | owner | ownership | High | Redact logs | Maybe | Tool use gates |

---

## 28. Agentic AI Architecture

**Deterministic app owns:** authentication, authorization, storage, validation, workflow state, provenance, privacy, billing, exports, notifications, human review gates.

**LLM/AI owns:** summaries, drafts, roadmap reasoning, interview question generation, study material generation, fit analysis, explanations, content transformation.

| Level | Meaning |
|---|---|
| 0 | Deterministic CRUD |
| 1 | Single structured LLM call |
| 2 | Routed workflow |
| 3 | Evaluator/optimizer |
| 4 | Tool-using workflow |
| 5 | Agent with human checkpoints |

**Rule:** Use the lowest level that can solve the task safely.

---

## 29. AI Feature Build Template

Define: user input; context allowed/forbidden; model/provider; structured schema; tool/function calls; validation; safety checks; source grounding; fallback; cost control; human review; logging restrictions; tests/evals.

---

## 30. AI Evaluation and Quality Gates

Gates: source grounding; schema validity; no hallucinated facts; no generic output; role/pathway specificity; safety/privacy; cost/token budget; human review for high-impact actions.

Apply to: CV generation; roadmap generation; interview pack generation; study material; job fit; application drafts; education/migration guidance.

---

## 31. Analytics and Observability Event Map

| Event | Purpose | Safe metadata | Forbidden | Privacy |
|---|---|---|---|---|
| subject_created | Foundation usage | subject_id hash | PII | OK |
| goal_created | Goal adoption | goal_kind, status | raw description optional omit | Prefer omit free text |
| passport_completed | Onboarding | completeness % | raw profile | OK |
| cv_created | CV funnel | template_id | CV body | No body |
| cv_exported | Export funnel | template_id | CV body | No body |
| roadmap_created | Roadmap funnel | pathway_type | free text | Prefer omit |
| roadmap_task_completed | Progress | task_id | notes | OK |
| job_saved | Opportunity funnel | source_site | full JD | No JD dump |
| job_fit_viewed | Fit usage | job_id | scores detail optional | Careful |
| interview_session_started | Prep funnel | role_slug | Q&A text | No Q&A |
| practice_completed | Practice funnel | skill_id | answers | No answers |
| application_draft_created | Apply funnel | draft_id | letter body | No body |
| application_submitted_after_review | Safe apply | draft_id | letter/CV body | No body |

Do not log sensitive raw content.

---

## 32. Testing and QA Strategy

**User-visible:** frontend typecheck/build; lint if configured; local backend+frontend; browser journey; console check; `frontend/dist` ignored check.

**Backend:** targeted tests; migration tests if schema changed; ownership/auth tests; fresh DB runtime when foundation/schema changes.

**AI:** golden examples; adversarial prompts; schema validation; source/freshness; generic-output checks; cost checks.

---

## 33. Browser Journey Test Matrix

| Feature | Journey | Start | Steps | Expected | Console | Persist | MVP required? |
|---|---|---|---|---|---|---|---|
| Auth | login | `/login` | credentials → dashboard | Lands dashboard | Clean | Session | Yes |
| Dashboard | load | `/dashboard` | open | Renders | Clean | — | Yes |
| Platform | subject create | `/platform` | create subject | Appears | Clean | Refresh | Yes |
| Platform | goal create | `/platform` | select → create goal | Appears | Clean | Refresh | Yes |
| CV | template select | `/cv-builder` | choose template | Selected | Clean | State | CVB-F2 |
| CV | preview | `/cv-builder` | open preview | Preview shows | Clean | — | CVB-F2 |
| CV | export | `/cv-builder` | export PDF | Download/open | Clean | File not tracked | CVB-F3/F5 |
| Roadmap | create | `/roadmaps` | create | Listed | Clean | Refresh | ROAD-F2 |
| Roadmap | task complete | `/roadmaps/:id` | complete task | Progress updates | Clean | Refresh | ROAD-F3 |
| Jobs | save | `/jobs` | save job | In saved | Clean | Refresh | Existing |
| Interview | session start | `/interview-studio` | start | Session open | Clean | — | Future |
| Applications | draft create | `/applications/drafts` | create | Draft saved | Clean | Refresh | Future |

---

## 34. Release and Feature Flag Strategy

Levels: hidden route → internal preview → beta → public → deprecated → removed.

Every large feature should show: status label; readiness; known limitations; what is not built yet.

---

## 35. MVP Build Strategy

| # | Step | Purpose | Why now | Allowed | Forbidden | Backend | Frontend | Browser | Commit | Tracker |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Master plan + live tracker | Operating system docs | Orientation | docs/product/* | product code | None | None | N/A | docs commit | Yes |
| 2 | Navigation/sitemap contract | Route contract | Before UI churn | docs (+ optional contract doc) | product code unless approved | None | Inspect only | N/A | docs | Yes |
| 3 | Design-system shell | Tokens/components | Before redesign | docs + audit | Broad rewrite | None | Audit | N/A | docs | Yes |
| 4 | Dashboard shell | Home honesty | Orientation | dashboard files if approved | Fake metrics | Aggregate reads | Shell | Load | feature | Yes |
| 5 | CV Builder stabilization | Visible value | Before 0051 | CVB files | AI agents | CV APIs | CV UI | Full CV journey | CVB commits | Yes |
| 6 | Roadmap stabilization | Pathway value | Before 0051 | ROAD files | Graduate-only ownership | Roadmap APIs | Roadmap UI | Roadmap journey | ROAD commits | Yes |
| 7 | Career Passport MVP | Identity | After taxonomy/passport slices | passport | Claims verify without rules | 0052 | passport UI | Passport journey | 0052 | Yes |
| 8 | Roadmap Engine MVP | Intelligence | After 0051 | roadmaps | Unsourced pathways | 0051+ | roadmaps | Generate journey | later | Yes |
| 9 | Opportunity Intelligence MVP | Fit | After 0054 | opportunities | Fake certainty | 0054–55 | opportunities | Fit journey | later | Yes |
| 10 | Interview Studio MVP | Prep | New system | interview_studio | 004E repair | 0061 | studio | Session journey | later | Yes |
| 11 | Skills→Practice→Proof MVP | Proof loop | After 0060 | skills/claims | Unverified badges | 0060 | skills | Proof journey | later | Yes |
| 12 | Applications / Safe Apply MVP | Safe apply | After gates | applications | Blind auto-apply | 0068 | applications | Review→submit | later | Yes |

---

## 36. Full Ladder With Technical Build Notes

| Slice ID | Slice Name | Goal | Why Now | Backend | Frontend | Data/Migration | AI | Security/Privacy | Tests | Browser | Evidence | Tracker | Master plan update? | Commit boundary | Push | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UX0-S1 | Master Build Plan + Live Tracker | Create two docs | Operating model | None | None | None | None | No secrets in docs | Doc existence | N/A | Desktop UX0-S1 evidence | Yes | Yes (create) | docs only | Yes | In progress |
| UX0-S2 | Navigation + Sitemap Contract | Route contract | Before nav changes | None | Inspect routes | None | None | Access types | Doc checks | N/A | UX0-S2 evidence | Yes | If nav map changes | docs | Yes | Planned |
| UX0-S3 | Design System + Component Inventory | Visual system | Before redesign | None | Audit components | None | None | A11y rules | Doc checks | N/A | UX0-S3 | Yes | If tokens change | docs | Yes | Planned |
| UX0-S4 | Domain Ownership Map | BE/FE owners | Before modules | Inspect packages | Inspect folders | None | None | Ownership rules | Doc checks | N/A | UX0-S4 | Yes | If map changes | docs | Yes | Planned |
| UX0-S5 | Ladder Checkpoint | Freeze next slices | Before CVB/ROAD | None | None | None | None | — | Doc checks | N/A | UX0-S5 | Yes | If ladder changes | docs | Yes | Planned |
| PF11-R1 | Platform Shell Review | Review `/platform` | Before Platform expansion | None unless bug | Inspect PlatformPage | None | None | Auth states | Build + journey | Platform journey | PF11-R1 | Yes | No unless arch change | optional fix only | If fix | Planned |
| CVB-F0 | CV Builder Audit | Audit only | Before repair | Inspect | Inspect | None | None | — | Manual audit | Open page | CVB-F0 | Yes | No | docs/evidence | Optional | Planned |
| CVB-F1 | CV Builder UI Repair | Usable page | After audit | Minimal | CV page | None | None | Auth | Build | Load/edit | CVB-F1 | Yes | No | CVB files | Yes | Planned |
| CVB-F2 | Template Gallery + Preview | Templates | After F1 | Minimal | Gallery/preview | None | No AI rewrite | — | Build | Template+preview | CVB-F2 | Yes | No | CVB files | Yes | Planned |
| CVB-F3 | PDF Export Verification | Export works | After F2 | Export path | Export UI | None | None | Safe filename | Build + open PDF | Export | CVB-F3 | Yes | No | CVB files | Yes | Planned |
| CVB-F4 | Save/Load Versions | Persist CVs | After F3 | Versions API | Save/load UI | Maybe | None | Ownership | API+UI tests | Save/refresh/load | CVB-F4 | Yes | If API contract | CV+API | Yes | Planned |
| CVB-F5 | CV Browser Checkpoint | Close CVB | After F3+F4 | — | — | — | — | — | Full | Full CV journey | CVB-F5 | Yes | No | evidence/docs | Yes | Planned |
| ROAD-F0 | Roadmap Audit | Audit only | Before repair | Inspect | Inspect | None | None | — | Manual | Open page | ROAD-F0 | Yes | No | docs | Optional | Planned |
| ROAD-F1 | Roadmap UI Repair | Usable list | After F0 | Minimal | Roadmap page | None | No full AI engine | — | Build | List/empty/CTA | ROAD-F1 | Yes | No | ROAD files | Yes | Planned |
| ROAD-F2 | Save/Load Contract | Persist roadmaps | After F1 | Roadmap APIs | Save/load | Maybe | None | Ownership | API tests | Create/refresh | ROAD-F2 | Yes | If contract | ROAD+API | Yes | Planned |
| ROAD-F3 | Detail + Tasks | Tracking | After F2 | Tasks API | Detail UI | Maybe | None | Ownership | API+UI | Complete task persist | ROAD-F3 | Yes | No | ROAD files | Yes | Planned |
| ROAD-F4 | Browser Checkpoint | Close ROAD | After F3 | — | — | — | — | — | Full | Full roadmap journey | ROAD-F4 | Yes | No | evidence | Yes | Planned |
| 0051 | Role & Pathway Taxonomy | Taxonomy | After UX0+CVB/ROAD stab | Taxonomy module | Consumers later | Yes | Structured | — | Migration+tests | N/A early | 0051 | Yes | Yes | foundation+module | Yes | Planned |
| 0052 | Career & Education Passport | Passport | After 0051 | passport | passport UI | Yes | L1 assist | High privacy | Tests | Passport journey | 0052 | Yes | Yes | module | Yes | Planned |
| 0053 | Claims & Evidence Graph | Evidence | After 0052 | claims/provenance UI | claims UI | Maybe | Validation | Provenance | Tests | Claim+source | 0053 | Yes | Yes | module | Yes | Planned |
| 0054 | Global Jobs & Opportunity Data | Sources | After honesty baseline | opportunities data | — | Yes | — | Source freshness | Tests | N/A | 0054 | Yes | Yes | module | Yes | Planned |
| 0055 | Opportunity Intelligence | Fit | After 0054 | fit services | opportunities UI | Maybe | L1–L2 | No fake certainty | Evals | Fit journey | 0055 | Yes | Yes | module | Yes | Planned |
| 0056 | Graduate Launch Navigator | Grad paths | After taxonomy | graduate_launch | graduate-launch | Yes | L1–L2 | — | Tests | Launch journey | 0056 | Yes | Yes | module | Yes | Planned |
| 0057 | Workplace Reality Engine | Reality signals | After 0055 | workplace | UI later | Yes | Grounded | Sources | Evals | — | 0057 | Yes | Yes | module | Yes | Planned |
| 0058 | Skills Demand Radar | Demand | After 0054 | skills demand | radar UI | Yes | L1 | Sources | Evals | — | 0058 | Yes | Yes | module | Yes | Planned |
| 0059 | Role Trials | Trials | After skills | trials | practice UI | Yes | L1 | — | Tests | Trial journey | 0059 | Yes | Yes | module | Yes | Planned |
| 0060 | Skill → Practice → Proof | Proof loop | Before mature studio | skills/proof | skills UI | Yes | L1 | Provenance | Tests | Proof journey | 0060 | Yes | Yes | module | Yes | Planned |
| 0061 | Interview Studio | New prep system | After 0060 baseline | interview_studio | studio UI | Yes | L1–L2 | Sources | Evals | Session journey | 0061 | Yes | Yes | module | Yes | Planned |
| 0062 | Outcome Learning Engine | Learn from outcomes | After applications | outcomes | dashboard | Yes | L1 | Privacy | Tests | — | 0062 | Yes | Yes | module | Yes | Planned |
| 0063 | Public Service Source Engine | Sources | Before gov UX | public_sector | — | Yes | — | Freshness | Tests | — | 0063 | Yes | Yes | module | Yes | Planned |
| 0064 | India Government Careers | India nav | After 0063 | public_sector | public-sector | Yes | Grounded | Jurisdiction | Tests | — | 0064 | Yes | Yes | module | Yes | Planned |
| 0065 | Adaptive Gov Exam Prep | Exam prep | After 0064 | public_sector | prep UI | Yes | L1–L2 | Sources | Evals | — | 0065 | Yes | Yes | module | Yes | Planned |
| 0066 | GCC Public Sector Navigator | GCC | After 0063 | public_sector | public-sector | Yes | Grounded | Jurisdiction | Tests | — | 0066 | Yes | Yes | module | Yes | Planned |
| 0067 | Public Service Finalization | Gate | After 0063–66 | — | — | — | — | — | Full | Journeys | 0067 | Yes | Yes | evidence | Yes | Planned |
| 0068 | Safe Application Platform | Safe apply | After review gates | applications | applications | Yes | L1 drafts | **Human review** | Auth+review tests | Review→submit | 0068 | Yes | Yes | module | Yes | Planned |
| 0069 | Global Education Source Engine | Education sources | Before study UX | education | — | Yes | — | Freshness | Tests | — | 0069 | Yes | Yes | module | Yes | Planned |
| 0070 | Study Abroad Navigator | Study abroad | After 0069 | education | study-abroad | Yes | Grounded | Sources | Tests | — | 0070 | Yes | Yes | module | Yes | Planned |
| 0071 | Language Requirement & Exam Engine | Language | After 0069 | education | language | Yes | Grounded | Sources | Tests | — | 0071 | Yes | Yes | module | Yes | Planned |
| 0072 | Masters/PhD & Research Navigator | Research paths | After 0069 | education | masters-phd | Yes | Grounded | Sources | Tests | — | 0072 | Yes | Yes | module | Yes | Planned |
| 0073 | Global Mobility Intelligence | Mobility | After geo+education | mobility | migration | Yes | Grounded | Jurisdiction | Tests | — | 0073 | Yes | Yes | module | Yes | Planned |
| 0074 | Browser/Email/Calendar/Notifications | Channels | After core MVP | notifications | shell | Yes | — | Consent | Tests | — | 0074 | Yes | Yes | module | Yes | Planned |
| 0075 | Subscription & Billing | Monetization | After core value | billing | billing | Yes | — | Audit | Tests | — | 0075 | Yes | Yes | module | Yes | Planned |
| 0076 | B2B/B2B2C | Partners | After consumer MVP | b2b | admin | Yes | — | RBAC | Tests | — | 0076 | Yes | Yes | module | Yes | Planned |
| 0077 | Localization & Regionalization | i18n | After core | i18n | UI strings | Maybe | — | Locale privacy | Tests | — | 0077 | Yes | Yes | module | Yes | Planned |
| 0078 | Security, Privacy & Compliance | Hardening | Continuous + gate | privacy | privacy UI | Maybe | — | Full matrix | Security tests | — | 0078 | Yes | Yes | module | Yes | Planned |
| 0079 | Scale & Observability | Scale | Before launch | observability | — | Maybe | Cost controls | Redaction | Load/obs tests | — | 0079 | Yes | Yes | module | Yes | Planned |
| 0080 | Final Platform Launch Gate | Launch | End | — | — | — | — | Full review | Full suite | Full journeys | 0080 | Yes | Yes | evidence | Yes | Planned |

---

## 37. Pre-Written Technical Execution Blueprint

### Universal Slice Execution Pattern

1. **Preflight** — branch, HEAD, origin/main, cached/staged, working tree; stop if unexpected dirty files.
2. **Read project docs** — live tracker then master plan; confirm phase/slice/next/frozen.
3. **Inspect relevant repo area** — routes, components, API client, types, backend routes/schemas/services/models/tests/migrations.
4. **Define allowed files** — exact paths; avoid generated/frozen areas.
5. **Implement or audit only the requested slice** — no opportunistic work, hidden cleanup, unrelated refactor, or out-of-scope redesign.
6. **Run checks matching risk** — docs-only / frontend-visible / backend-API / schema-migration / AI evals.
7. **Update live tracker** — position, status, files, tests, evidence, commit, next slice.
8. **Produce Desktop evidence file** — timestamp, HEAD, branch, origin comparison, files, tests, browser, git status, verdict.
9. **Stage only approved files** — no `git add .` / `-A`; explicit paths only.
10. **Commit only when acceptance allows** — one slice per commit where possible; verify; push after verification unless paused.

---

## 38. Universal Technical Gate Before Any Feature

Before implementing any feature, define:

```text
Feature / Route / Navigation group / User problem
Backend module owner / Frontend feature owner
Primary models / Primary APIs
Auth requirement / Object ownership rule
Privacy classification / Provenance requirement
AI involvement level
UI components / UI states / Browser journey
Allowed files / Forbidden files / Tests
Evidence file / Commit boundary / Rollback note
```

If missing → `BLOCKED_MISSING_FEATURE_GATE`.

---

## 39. Backend Implementation Template

Target shape:

```text
backend/app/<module_name>/
  __init__.py models.py schemas.py service.py routes.py
  tests/test_<module>_routes.py tests/test_<module>_service.py
  README.md
```

Routes: request/response schemas; auth dependency; ownership check; service call; error model; privacy/provenance; tests.

Services: purpose; inputs/outputs; ownership assumptions; validation; DB reads/writes; side effects; failure behavior.

Schema-changing slices: migration; upgrade path; downgrade or documented no-downgrade; fresh DB check; model/schema alignment tests.

---

## 40. Frontend Implementation Template

Target shape:

```text
frontend/src/features/<feature_name>/
  components/ hooks/ pages/ types.ts api.ts index.ts
```

If current repo does not yet support this, use current structure but document the target.

Every page: route; page component; API methods; types; components; server/form/UI state; loading/empty/error/unauthorized/success; mobile; browser journey.

---

## 41. API Contract Template

```text
Endpoint / Method / Purpose / Auth / Owner check
Request schema / Response schema / Success status
Error cases / Privacy note / Provenance note
Frontend caller / Backend service / Tests
```

Minimum errors: 401, 403, 404, 422, 500 (safe message).

---

## 42. AI Feature Template

```text
AI feature name / User-facing purpose / Input
Allowed context / Forbidden context
Model/provider / Prompt owner / Structured output schema
Tool/function calls / Validation / Evaluator
Fallback / Human review / Cost control / Rate limit
Privacy/logging restrictions / Tests/evals
```

**Always human review:** CV export; application submission; claim verification; job application email; migration/visa guidance; education application guidance; public-sector deadline/eligibility guidance.

---

## 43. Detailed Technical Slice Cards

### UX0-S2 — Navigation + Sitemap Contract
- **Goal / non-tech:** Turn master navigation into a concrete route contract.
- **Tech purpose:** Map existing vs planned routes, access, breadcrumbs, sidebar groups.
- **Prerequisites:** UX0-S1 complete.
- **Allowed:** `docs/product/careerkundi_live_tracker.md`, master plan if nav map changes, optional approved route-contract doc.
- **Forbidden:** product code unless explicitly approved; `frontend/dist`; backend; frozen 004E/Auto Apply.
- **Backend/Frontend/API/DB/AI:** None / inspect only / none / none / none.
- **Security:** document access types.
- **Tests:** doc existence + status. **Browser:** no.
- **Tracker update:** required. **Master plan update:** only if nav map changes.
- **Evidence:** `~/Desktop/CareerKundi_UX0_S2_Navigation_Sitemap_Evidence.txt`
- **Done:** route contract table complete; statuses existing/planned/placeholder/deferred.
- **Commit message suggestion:** `docs(product): add navigation and sitemap contract`
- **Push:** yes after verification. **Rollback:** revert docs commit.
- **Product code changes allowed:** No (unless explicitly approved).

### UX0-S3 — Design System + Component Inventory
- **Goal:** Define visual system before redesign.
- **Allowed:** docs (+ component inventory in docs). **Forbidden:** broad UI rewrite.
- **Tasks:** audit layout/shared components; list reusable/missing; tokens; layout zones; a11y; prioritize CV/Roadmap components.
- **Implementation allowed:** audit/docs only unless approved.
- **Evidence:** `~/Desktop/CareerKundi_UX0_S3_Design_System_Evidence.txt`
- **Commit suggestion:** `docs(product): add design system and component inventory`

### UX0-S4 — Backend/Frontend Domain Ownership Map
- **Goal:** Connect features to modules/folders/APIs/models/security/tests.
- **Tasks:** inspect backend/frontend dirs; map existing/planned; gaps; ownership + service-contract rules.
- **Evidence:** `~/Desktop/CareerKundi_UX0_S4_Domain_Ownership_Evidence.txt`
- **Commit suggestion:** `docs(product): add domain ownership map`

### UX0-S5 — Implementation Ladder Checkpoint
- **Goal:** Freeze next 10–15 slices and commit boundaries.
- **Tasks:** confirm order; PF11-R1 need; CVB/ROAD order; exact next slice; evidence naming.
- **Evidence:** `~/Desktop/CareerKundi_UX0_S5_Ladder_Checkpoint_Evidence.txt`
- **Commit suggestion:** `docs(product): freeze next implementation ladder`

### PF11-R1 — Platform Shell Review / Refinement
- **Goal:** Review committed `/platform` against master UI architecture.
- **Allowed:** Platform page/nav files only if refinement approved; else docs/evidence.
- **Tasks:** inspect route, sidebar, breadcrumb, layout; subjects/goals only; L/E/E states; browser journey.
- **Browser:** required. **Evidence:** `~/Desktop/CareerKundi_PF11_R1_Platform_Shell_Review_Evidence.txt`
- **Commit:** only if approved fixes. **Push:** if committed.

### CVB-F0 — CV Builder Audit
- **Implementation allowed:** No.
- **Tasks:** find routes/components/types/API/PDF; run page; document breaks; define F1–F5.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F0_CV_Builder_Audit_Evidence.txt`

### CVB-F1 — CV Builder UI Repair
- **Goal:** Page loads cleanly and is usable.
- **Tasks:** route exists; no crash; sections display; L/E/E; fix imports/types; no advanced AI.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F1_UI_Repair_Evidence.txt`
- **Commit suggestion:** `fix(cv-builder): repair CV Builder UI shell`

### CVB-F2 — Template Gallery + Preview
- **Goal:** Template selection + preview-before-download.
- **Tasks:** template metadata; gallery; ATS + modern templates; live preview; selected template state; no AI rewriting unless approved.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F2_Templates_Preview_Evidence.txt`
- **Commit suggestion:** `feat(cv-builder): add template gallery and preview`

### CVB-F3 — CV PDF Export Verification
- **Goal:** Stabilize PDF export.
- **Tasks:** inspect PDF approach; template exports; safe filename; opens/downloads; no generated files tracked.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F3_PDF_Export_Evidence.txt`
- **Commit suggestion:** `fix(cv-builder): verify and stabilize PDF export`

### CVB-F4 — CV Save/Load Versions
- **Goal:** Persist CV versions.
- **Possible API:** `GET/POST /api/v1/cv-builder/versions`, `GET/PATCH /api/v1/cv-builder/versions/{id}` (planned, not claimed existing).
- **Rules:** belongs to authenticated user/subject; ownership checks.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F4_Save_Load_Evidence.txt`
- **Commit suggestion:** `feat(cv-builder): add CV version save and load`

### CVB-F5 — CV Browser-Tested Checkpoint
- **Goal:** Close CV stabilization with website verification.
- **Browser:** login → CV Builder → template → edit → preview → save → refresh → load → export PDF.
- **Evidence:** `~/Desktop/CareerKundi_CVB_F5_Browser_Checkpoint_Evidence.txt`

### ROAD-F0 — Roadmap Audit
- **Implementation allowed:** No.
- **Tasks:** find routes/components/APIs; run page; document behavior; compare to platform-wide placement; define F1–F4.
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F0_Roadmap_Audit_Evidence.txt`

### ROAD-F1 — Roadmap UI Repair
- **Goal:** Load usable surface; list or empty; create CTA; no full AI engine; no Graduate Launch ownership confusion.
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F1_UI_Repair_Evidence.txt`
- **Commit suggestion:** `fix(roadmaps): repair Roadmap UI shell`

### ROAD-F2 — Roadmap Save/Load Contract
- **Possible API:** `GET/POST /api/v1/roadmaps`, `GET/PATCH /api/v1/roadmaps/{id}`, `POST .../tasks`, `PATCH .../tasks/{task_id}` (planned).
- **Rules:** belongs to user/subject; ownership; no cross-user access.
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F2_Save_Load_Evidence.txt`
- **Commit suggestion:** `feat(roadmaps): add roadmap save and load contract`

### ROAD-F3 — Roadmap Detail + Task Tracking
- **Goal:** Detail with milestones, tasks, completion, progress, persistence.
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F3_Detail_Tasks_Evidence.txt`
- **Commit suggestion:** `feat(roadmaps): add roadmap detail and task tracking`

---

## 44. Key Technical Slice Notes

See Section 43 cards for UX0-S2…ROAD-F3. Additional emphasis:

- **UX0-S2:** backend none; frontend inspect only unless approved.
- **PF11-R1:** verify subjects/goals only; no claims UI creep.
- **CVB-F0 / ROAD-F0:** implementation not allowed.
- **CVB-F4 / ROAD-F2:** ownership checks mandatory on every object route.

---

## 45. Anti-Drift Controls

- Do not jump ahead in the ladder.
- Do not implement before route/backend/frontend/API/test ownership is defined.
- Do not mix unrelated features in one slice.
- Do not repair old frozen systems unless explicitly reactivated.
- Do not add AI agents where deterministic logic is enough.
- Do not create duplicate planning documents.
- Do not modify unrelated files.
- Do not treat planned features as completed.
- Do not claim browser verification unless a browser journey was actually run.
- Do not claim source-backed facts unless the source was preserved.

Violation → `BLOCKED_SCOPE_DRIFT`.

---

## 46. Slice Acceptance Status

| Status | Meaning |
|---|---|
| PASS_ACCEPTED | Required work done; evidence clean; tests match risk; tracker updated; commit/push verified if required |
| PARTIAL_ACCEPTED_WITH_LIMITATIONS | Usable core; non-blocking limitations documented |
| NEEDS_FIX | Close, but issues must be corrected |
| BLOCKED | Missing dependency, dirty repo, test failure, unknown route/API, migration/auth issue, unclear requirement |
| REJECTED | Violates architecture, scope, safety, data integrity, or product direction |

---

## 47. Recovery Playbook

| Issue | Action |
|---|---|
| Unexpected dirty repo | Stop; capture `git status`; classify; do not destructive-clean |
| Unexpected staged files | Stop; show cached names; unstage only with explicit user-approved narrow command if provided; else block |
| Frontend build failure | Capture error; fix only allowed files |
| Browser journey failure | Capture screenshot/console; fix allowed files or block |
| Backend test failure | Capture failing test; fix allowed files or block |
| Migration failure | Stop; do not force; document; block |
| Push failure | Capture remote error; do not force-push; block |

Rules: stop immediately; no destructive git; capture exact status/error; classify; fix only within allowed files; otherwise mark blocked.

---

## 48. Decision Record Template

```text
## Decision Record — <ADR-ID>

Date:
Decision:
Context:
Options considered:
Chosen option:
Reason:
Impact:
Risk:
Rollback / revisit condition:
Status:
```

Use for: CV Builder before 0051; Roadmaps platform-wide; Interview Studio as new system; Safe Apply replacing Auto Apply; MCP deferred; AI agents only after deterministic workflows.

---

## 49. Dependency Map

- UX0-S1 → before UX0-S2
- UX0-S2 → before major navigation changes
- UX0-S3 → before large UI redesign
- UX0-S4 → before new backend feature modules
- UX0-S5 → before CV Builder and Roadmap stabilization
- PF11-R1 → before expanding Platform UI
- CVB-F0 → CVB-F1 → CVB-F2 → CVB-F3/F4 → CVB-F5
- ROAD-F0 → ROAD-F1 → ROAD-F2 → ROAD-F3
- 0051 → before serious Passport/Roadmap/Opportunity taxonomy intelligence
- 0052 → before deep CV/roadmap personalization and applications depth
- 0053 → before evidence-backed claims/proof workflows
- 0054 → before source-backed Opportunity Intelligence
- 0060 → before mature Interview Studio and proof/badge systems
- 0068 → only after Safe Apply rules and human review gates finalized

---

## 50. Do-Not-Build-Yet Register

- Do not rebuild old 004E Interview Pack.
- Do not revive old Auto Apply / blind auto-apply / autonomous application submission.
- Do not add claims verification without evidence rules.
- Do not add public-sector deadlines without source freshness.
- Do not add migration/visa guidance without jurisdiction/source rules.
- Do not add MCP before core workflows stabilize.
- Do not add full autonomous agents before deterministic workflows and human checkpoints.
- Do not add billing before core MVP value is usable.
- Do not do a giant frontend folder rewrite without a dedicated slice.

---

## 51. Evidence Quality Checklist

Every evidence file should include: timestamp; HEAD before; HEAD after if committed; branch; origin/main comparison; files changed; allowed/forbidden checks; tests + results; browser journey if required; console summary if browser-tested; `frontend/dist` status if build ran; live tracker update status; master plan update status if relevant; commit hash if committed; push verification if pushed; known limitations; final verdict.

---

## 52. Human Review Gates

Required before: committing feature code; pushing feature code; destructive git; editing applied migrations; changing auth/security/privacy/retention; sending emails; submitting applications; claiming verification; exporting final CV/application documents; activating paid billing; enabling autonomous agents.

---

## 53. Future Prompt Template

```text
# CAREERKUNDI — <SLICE_ID>
## <SLICE_NAME>

Recommended model:
Cursor mode:
Effort:
Purpose:

Current repo checkpoint:
Live tracker status:
Master plan reference:
Prerequisites:
Allowed files:
Forbidden files:
Tasks:
Backend tasks:
Frontend tasks:
API tasks:
Database/migration tasks:
AI tasks:
Security/privacy tasks:
Live tracker update required:
Master plan update required:
What not to build:
Tests:
Browser journey:
Evidence file:
Required final response:
Commit rule:
Push rule:
```

---

## 54. Live Tracker Update Template

```text
## Tracker Update — <SLICE_ID>

Date:
Slice:
Status:
Summary:
Files changed:
Tests run:
Browser journey:
Evidence file:
Commit:
Push:
Next slice:
Blockers:
Decision needed:
```

---

## 55. Prompt Generation Rule

When generating future Cursor prompts:

1. Read `docs/product/careerkundi_live_tracker.md`.
2. Read `docs/product/careerkundi_master_build_plan.md`.
3. Identify the exact next slice.
4. Copy the matching technical slice card.
5. Add current checkpoint/HEAD from latest evidence.
6. Add exact allowed files.
7. Add exact forbidden files.
8. Add tests based on risk.
9. Add browser journey if user-visible.
10. Add live tracker update requirement.
11. Add master plan update requirement only if architecture changes.
12. Add evidence file requirement.
13. Add commit/push rule.

---

*End of CareerKundi Master Build Plan (UX0-S1).*
