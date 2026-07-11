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

## UX0-S3 Design System + Component Inventory

**Slice:** UX0-S3  
**Date:** 2026-07-11  
**Type:** Docs-only design system + component inventory contract (no CSS/component implementation in this slice)  
**Inspected (read-only):** `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/**`, `frontend/src/pages/**`, `frontend/src/styles/**`, `frontend/src/store/**`, `frontend/src/lib/api.ts`, `frontend/src/types/api.ts`, `frontend/vite.config.ts`

### 6.1 Current Frontend Design Inventory

| Area | Verified Files / Folders | Current Role | Current Status | Notes |
|---|---|---|---|---|
| Routing shell | `App.tsx`, `main.tsx` (`BrowserRouter`) | Public vs Private routes + lazy pages | EXISTING_VERIFIED | No `index.css` / `App.css` at src root |
| Layout components | `components/layout/AppShell.tsx` + `.module.css` | Sidebar + header + content + chatbot FAB + toasts | EXISTING_VERIFIED | |
| Sidebar | `components/layout/Sidebar.tsx` + `.module.css` | Auth nav groups | EXISTING_VERIFIED | Groups differ from UX0-S2 target map |
| Header / topbar | `components/layout/Header.tsx` + `.module.css` | Breadcrumb, theme toggle, user menu | EXISTING_VERIFIED | |
| Page components | `pages/*.tsx` (14 page files) | Route-level screens | EXISTING_NEEDS_REVIEW | Includes unmounted `InterviewPackPage.tsx` |
| Global CSS / tokens | `styles/globals.css` | Design tokens, reset, utilities | EXISTING_VERIFIED | Dark/light via `[data-theme]` |
| Motion CSS | `styles/animations.css` | Shared animations | EXISTING_VERIFIED | |
| Feature page CSS | `styles/feature-pages.css` | Cross-page feature styles | EXISTING_NEEDS_REVIEW | Prefer tokens over one-off styles over time |
| Shared UI kit | `components/ui/*` + `index.ts` | Button, Card, Badge, Input, Textarea, Modal, Spinner, Toast | EXISTING_VERIFIED | CSS modules per component |
| Feature components | `components/features/*` | Jobs/CV/interview/radar panels | EXISTING_NEEDS_REVIEW | Job-heavy; CV/Roadmap mostly page-local |
| Chatbot | `components/chatbot/ChatbotWidget.tsx` | FAB assistant | EXISTING_VERIFIED | Also `/chatbot` page |
| Theme / design-system folder | — | — | MISSING | No `src/theme/` or `src/design-system/` |
| Tailwind / PostCSS | — | — | MISSING | No `tailwind.config.*` / `postcss.config.*` |
| UI state stores | `store/auth.ts`, `store/ui.ts` | Auth + theme/sidebar/toasts/chatbot | EXISTING_VERIFIED | Zustand |
| API/types affecting UI | `lib/api.ts`, `types/api.ts` | Typed API client + envelopes | EXISTING_VERIFIED | Platform + legacy domains |
| Build / styling tooling | Vite 5, `@vitejs/plugin-react`, CSS modules, `clsx`, `framer-motion`, `lucide-react`, `recharts` | Bundler + motion + icons + charts | EXISTING_VERIFIED | No new UI library without ADR |

### 6.2 Current Component Inventory

| Component / Pattern | Source File | Current Use | Shared or Feature-Specific | Reuse Candidate? | Notes |
|---|---|---|---|---|---|
| AppShell | `layout/AppShell.tsx` | Authenticated chrome | Shared | Yes | Keep stable |
| Sidebar | `layout/Sidebar.tsx` | Nav | Shared | Yes | Remap after UX0-S3+ via explicit slice |
| Header / Breadcrumb | `layout/Header.tsx` | Crumbs + theme + user | Shared | Yes | Expand `PAGE_LABELS` as routes land |
| Button | `ui/Button.tsx` | Primary/secondary/ghost/danger | Shared | Yes | Exists |
| Card (+ Header/Title/Content/Footer) | `ui/Card.tsx` | Surfaces | Shared | Yes | Exists |
| Badge | `ui/Badge.tsx` | Status chips | Shared | Yes | Exists |
| Input / Textarea | `ui/Input.tsx` | Forms | Shared | Yes | Exists |
| Modal | `ui/Modal.tsx` | Dialogs | Shared | Yes | Treat as Dialog family |
| Spinner | `ui/Spinner.tsx` | Loading | Shared | Yes | Exists |
| Toast / ToastContainer | `ui/Toast.tsx` | Feedback | Shared | Yes | Wired in AppShell |
| Login / Register patterns | `pages/LoginPage.tsx`, `RegisterPage.tsx` | Auth forms | Feature (auth) | Partial | Uses Input/Button |
| Landing pattern | `pages/LandingPage.tsx` | Public marketing | Feature | Low | |
| Dashboard pattern | `pages/DashboardPage.tsx` | Home | Feature | Needs review | EXISTING_NEEDS_REVIEW |
| Platform page cards/forms | `pages/PlatformPage.tsx` | Subjects + goals | Feature | Yes for L/E/E patterns | PF11 shell |
| Jobs page patterns | `pages/JobSearchPage.tsx` + `features/Job*` | Discovery/saved/filters/forms | Feature-specific | Selective | Heavy surface |
| JobDiscoveryPanel | `features/JobDiscoveryPanel.tsx` | Live discovery | Feature | No (jobs) | |
| JobDetailsForm | `features/JobDetailsForm.tsx` | Job edit form | Feature | No (jobs) | |
| SavedJobFilters | `features/SavedJobFilters.tsx` | Saved search filters | Feature | No (jobs) | |
| PopularJobRolesPanel | `features/PopularJobRolesPanel.tsx` | Role catalog UI | Feature | No (jobs) | |
| MatchScoreRing / SkillRadar | `features/MatchScoreRing.tsx`, `SkillRadar.tsx` | Score/radar visuals | Feature | Maybe later | Charts |
| InterviewPackView | `features/InterviewPackView.tsx` | Pack display | Feature | Frozen direction | Do not expand 004E repair |
| DefaultCVSelector | `features/DefaultCVSelector.tsx` | CV pick | Feature (CV) | Yes for CVB | |
| CV Builder page | `pages/CVBuilderPage.tsx` | CV editing | Feature | Audit CVB-F0 | EXISTING_NEEDS_REVIEW |
| Roadmap page | `pages/RoadmapPage.tsx` | Roadmap UI | Feature | Audit ROAD-F0 | EXISTING_NEEDS_REVIEW |
| Profile / Settings | `pages/ProfilePage.tsx`, `SettingsPage.tsx` | Account | Feature | Partial shared forms | |
| Achievements | `pages/AchievementsPage.tsx` | Badges gallery | Feature | Low priority re-home | |
| Chatbot page / widget | `pages/ChatbotPage.tsx`, `chatbot/ChatbotWidget.tsx` | Assistant | Feature → future panel | Later | |
| Tabs | — | — | Shared (planned) | Yes | MISSING as shared |
| Drawer | — | — | Shared (planned) | Yes | MISSING |
| Command palette | — | — | Shared (planned) | Later | MISSING |
| Select / Date picker | — | — | Shared (planned) | Yes | MISSING as shared (native `<select>` used ad hoc on Platform) |
| Progress / Timeline / Stepper | — | — | Shared (planned) | Roadmaps | MISSING |
| Data table | — | — | Shared (planned) | Applications later | MISSING |
| Skeleton | — | — | Shared (planned) | Yes | MISSING (Spinner used) |
| Dedicated Empty/Error state components | — | Inline per page | Shared (planned) | Yes | PARTIAL patterns; no shared primitives |
| Evidence card | — | — | Feature (claims) | Later | MISSING |
| Roadmap milestone card | — | — | Feature (roadmaps) | ROAD-F3 | MISSING |
| Opportunity card | Partial job cards | Jobs UI | Feature | Evolve | VERIFY_IN_REPO exact card abstraction |
| CV preview frame | — | — | Feature (CV) | CVB-F2 | MISSING / VERIFY_IN_REPO |
| Assistant panel (shell) | Chatbot FAB only | Global | Shared (planned) | Later | PARTIAL |

### 6.3 Target Design System Principles

**Visual direction:** modern, premium, clean, trustworthy, career-focused, slightly futuristic, accessible, mobile-responsive.

**Principles:**

- Consistency before decoration.
- Semantic layout before visual effects.
- Accessible contrast and focus states.
- Clear hierarchy; minimal cognitive load.
- Responsive from the start.
- Status states must be obvious.
- AI outputs must be visually distinguished from verified / user-provided data.
- Prefer existing CSS custom properties in `globals.css` over introducing a new UI library.

### 6.4 Design Tokens Contract

Do **not** implement new tokens in code during UX0-S3. Catalog current vs target rules.

| Token Category | Purpose | Current Status | Target Rule | Notes |
|---|---|---|---|---|
| Colors | Brand, surfaces, text, borders | EXISTING_VERIFIED in `globals.css` (`--bg-*`, `--accent-*`, `--text-*`, `--border-*`) | Keep CSS variables; avoid hard-coded one-offs in new UI | Dark default + light theme |
| Typography | Heading/body/mono + size scale | EXISTING_VERIFIED (`--font-*`, Major Third scale) | Use token scale only | Space Grotesk / Plus Jakarta Sans / JetBrains Mono |
| Spacing | Rhythm | EXISTING_VERIFIED (`--space-*`) | Prefer spacing tokens | |
| Border radius | Corners | EXISTING_VERIFIED (`--radius-*`) | Prefer tokens | |
| Shadows / elevation | Depth | EXISTING_VERIFIED (`--shadow-*`) | Restrain glow; no stack explosion | |
| Surface levels | base/surface/elevated/overlay/glass | EXISTING_VERIFIED | Map components to surface tokens | |
| Status colors | success/warn/danger/info | EXISTING_PARTIAL (`--accent-emerald/amber/rose/cyan`) | Semantic aliases (`--status-*`) planned later without breaking existing | Do not rename blindly |
| Focus states | Keyboard focus | EXISTING_NEEDS_REVIEW | Visible focus ring required everywhere | Utility focus ring mentioned in globals header — VERIFY_IN_REPO coverage |
| Motion / animation | Transitions | EXISTING_VERIFIED (`--transition-*` + `animations.css` + framer-motion) | Prefer meaningful motion; avoid noise | |
| Breakpoints | Responsive | VERIFY_IN_REPO | Document standard breakpoints before large redesign | Likely CSS media in modules |
| Z-index / layers | Stacking | EXISTING_VERIFIED (`--z-*`) | Keep single ladder | sidebar/header/modal/toast/chatbot |

### 6.5 Core Shared Component Contract

| Component | Purpose | Used In | MVP Priority | Accessibility Requirement | Implementation Slice |
|---|---|---|---|---|---|
| Button | Actions | All forms/CTAs | Existing | Keyboard, disabled, loading label | Existing; extend only if needed |
| Card | Surfaces | Lists/panels | Existing | Heading structure inside | Existing |
| Badge | Status | Jobs, achievements, later claims | Existing | Not color-only | Existing + semantic status later |
| Tabs | Section switch | CV/Roadmap/Studio later | High after audits | Arrow keys, `aria-selected` | PLANNED shared extract |
| Dialog (Modal) | Confirm/export | CV export, destructive | Existing Modal | Focus trap, Esc | Existing Modal |
| Drawer | Mobile nav / panels | Mobile later | Medium | Focus trap | PLANNED |
| Toast | Transient feedback | AppShell | Existing | Don’t rely on toast alone for errors | Existing |
| Command palette | Global jump | Future | Deferred | Full keyboard | DEFERRED |
| Sidebar | Nav | AppShell | Existing | `aria-label`, collapse label | Existing; remap later |
| Breadcrumb | Wayfinding | Header | Existing | `nav` + current page | Existing |
| Input / Textarea | Forms | Auth, Platform, Settings | Existing | Labels, errors | Existing |
| Select | Enum fields | Platform goal kind (native) | High for shared | Label association | PLANNED shared Select |
| Date picker | Dates | Goals/passport later | Medium | Keyboard | PLANNED |
| Progress | Completion | Roadmaps | High for ROAD | `aria-valuenow` | PLANNED |
| Timeline / Stepper | Pathway steps | Roadmaps | High for ROAD | Semantic order | PLANNED |
| Data table | Trackers | Applications later | Medium | Sortable a11y later | PLANNED |
| Skeleton | Loading placeholder | Lists | Medium | Pair with status text | PLANNED |
| Empty state | No data CTA | Platform, lists | High | Clear next action | PLANNED shared pattern |
| Error state | Failures | All pages | High | `role="alert"` | PLANNED shared pattern |
| Evidence card | Claims/sources | Passport/proof | Later | Status + source | After 0053 |
| Roadmap milestone card | Milestones | Roadmaps | High for ROAD-F3 | Progress clarity | ROAD-F3 |
| Opportunity card | Job/opportunity | Jobs | High | Title/company hierarchy | Evolve from jobs UI |
| CV preview frame | Live preview | CV Builder | High for CVB-F2 | Readable preview | CVB-F2 |
| Assistant panel | Contextual help | Shell | Medium | Esc/close, no sensitive dump | Later (evolve chatbot) |

### 6.6 Feature-Specific Component Inventory

| Feature | Required Components | Existing Components | Missing Components | MVP Priority | Notes |
|---|---|---|---|---|---|
| Platform | Subject list, goal form, L/E/E | PlatformPage + Card/Button/Input/Spinner/Toast | Shared Empty/Error primitives | High | Subjects/goals only |
| Dashboard | Snapshot, next actions, links | DashboardPage | Honest widgets; Empty | High | No fake metrics |
| CV Builder | Sections, template gallery, preview, export | CVBuilderPage, DefaultCVSelector | Template gallery, preview frame, version list | High | CVB-F0→F5 |
| Roadmaps | List, detail, milestones, tasks, progress | RoadmapPage | Milestone card, timeline, task row | High | ROAD-F0→F3; platform-wide |
| Career Passport | Section nav, forms | ProfilePage (partial) | Passport section shell | Medium | After 0052 |
| Opportunities | Search, filters, cards | JobSearchPage + Job* features | Dedicated Opportunity card abstraction | High (jobs) | Not full 0055 yet |
| Interview Studio | Session, Q panel, study | InterviewPackView (legacy) | Studio shell | Medium | New system; 004E frozen |
| Applications | Tracker table, draft editor, review gate | — | Table, draft, review UI | Medium | After 0068; no Auto Apply |
| Education / Mobility | Info cards, checklists | — | Level-1 placeholders | Low | FUTURE_FEATURE |
| Settings | Forms, toggles | SettingsPage | Privacy panels | Medium | Billing deferred |

### 6.7 Accessibility Contract

**Minimum requirements (planned):** keyboard navigation; visible focus states; semantic headings; form labels; error messages tied to fields; contrast-safe text; button/link distinction; loading announcements where appropriate; empty states with clear next action; mobile-readable layout; no color-only status communication.

| Area | Status |
|---|---|
| Overall WCAG claim | Do **not** claim WCAG compliance until tested |
| Shared UI kit (Button/Input/Modal labels) | ACCESSIBILITY_PARTIAL |
| Focus ring coverage across pages | VERIFY_IN_REPO |
| Platform L/E/E alerts | ACCESSIBILITY_PARTIAL (`role="alert"` used on Platform) |
| Full keyboard nav audit | ACCESSIBILITY_PLANNED |
| Contrast audit (dark/light) | ACCESSIBILITY_PLANNED |

### 6.8 UI State Contract

Every future user-visible page must define:

- loading state  
- empty state  
- error state  
- unauthorized state  
- success state  
- saving/submitting state  
- disabled state  
- mobile state  

**Rule:** No user-visible feature is accepted unless its key UI states are implemented or explicitly deferred with a reason.

### 6.9 Design System Implementation Order

1. UX0-S3 document-only inventory (**this slice**)  
2. UX0-S4 backend/frontend ownership map  
3. UX0-S5 ladder checkpoint  
4. PF11-R1 review / small shell refinements  
5. CVB-F0 audit  
6. CVB-F1 CV Builder UI repair using approved design patterns  
7. ROAD-F0 audit  
8. ROAD-F1 Roadmap UI repair using approved design patterns  
9. Shared component extraction only after repeated patterns are verified  

**Rules:**

- Do not extract shared components too early.  
- Do not do a giant visual rewrite.  
- Do not introduce a new UI library unless approved through a dedicated decision record.

### 6.10 UX0-S3 Implementation Decision

UX0-S3 is a **docs-only** design system and component inventory contract.

- No design implementation is included in this slice.  
- No CSS rewrite, component creation, or UI redesign is included in this slice.  
- Future design implementation must happen through **explicit frontend slices after UX0-S3 and UX0-S5**.  
- Prefer extending the existing token + CSS-module system over a new framework.

---

## UX0-S4 Backend / Frontend Domain Ownership Map

**Slice:** UX0-S4  
**Date:** 2026-07-11  
**Type:** Docs-only domain ownership contract (no product code, migrations, or folder moves)  
**Inspected (read-only):** `backend/app/main.py`, `backend/app/api/routes/*`, `backend/app/platform/*`, `backend/app/db/*`, `backend/app/agents/*`, `backend/app/schemas/*`, `backend/app/services/*`, `backend/pyproject.toml`, `frontend/src/{App,main}.tsx`, `frontend/src/components/**`, `frontend/src/pages/**`, `frontend/src/{lib,types,store,styles}/**`

### 7.1 Current Backend Module Inventory

| Backend Area | Verified Path | Current Purpose | Current Status | Owned Domain | Notes |
|---|---|---|---|---|---|
| App entry / routers | `backend/app/main.py` | FastAPI app; includes `/api/v1` routers | EXISTING_VERIFIED | platform + legacy domains | Routers: health, auth, profile, job_search, role_packs, cv_builder, roadmap, chatbot, apply, badges, queue, platform |
| API deps | `backend/app/api/deps.py` | Auth/user dependencies | EXISTING_VERIFIED | auth | |
| Platform API | `backend/app/api/routes/platform.py` | Subjects + goals envelopes | EXISTING_VERIFIED | Platform Foundation | PF8 |
| Platform subjects shim | `backend/app/api/routes/platform_subjects.py` | Re-exports platform router | EXISTING_VERIFIED | Platform Foundation | Compatibility only |
| Auth / profile / badges / queue / health / role_packs | `backend/app/api/routes/*.py` | Legacy product APIs | EXISTING_NEEDS_REVIEW | Settings / Jobs / CV / Roadmaps / Assistant | Per-route review later |
| Job search API | `backend/app/api/routes/job_search.py` | Discover/save/interview-pack | EXISTING_NEEDS_REVIEW | Opportunities / Jobs | Interview-pack endpoints ≠ Interview Studio |
| CV Builder API | `backend/app/api/routes/cv_builder.py` | CV routes | EXISTING_NEEDS_REVIEW | CV Builder | Audit in CVB-F0 |
| Roadmap API | `backend/app/api/routes/roadmap.py` | Roadmap routes | EXISTING_NEEDS_REVIEW | Roadmaps | Platform-wide; not Graduate-only |
| Apply API | `backend/app/api/routes/apply.py` | Apply flows | FROZEN / EXISTING_NEEDS_REVIEW | Applications (legacy) | Old Auto Apply direction frozen; do not expand as Safe Apply |
| Chatbot API | `backend/app/api/routes/chatbot.py` | Chat | EXISTING_NEEDS_REVIEW | AI Career Assistant | Evolve carefully |
| DB session / base | `backend/app/db/session.py`, `base.py` | Async DB | EXISTING_VERIFIED | infrastructure | |
| Legacy Alembic | `backend/app/db/migrations/` | Legacy migration lineage | EXISTING_NEEDS_REVIEW | infrastructure | Prefer foundation lineage for 0050+ |
| Foundation migrations | `backend/app/db/foundation_migrations/` | 0050 foundation revisions | EXISTING_VERIFIED | Platform Foundation | Do not edit casually |
| Migration runner | `backend/app/db/migration_runner.py` | Fail-closed runner | EXISTING_VERIFIED | infrastructure | |
| ORM models | `backend/app/db/models/*` | Users, jobs, CV, roadmap, claims, lifecycle, geo, privacy, etc. | EXISTING_VERIFIED | multi-domain | Split ownership by table in §7.7 |
| Platform kernel | `backend/app/platform/kernel/` | Kernel primitives | EXISTING_VERIFIED | Platform Foundation | |
| Platform identity | `backend/app/platform/identity/` | Subjects / actor refs | EXISTING_VERIFIED | Platform Foundation | |
| Platform provenance | `backend/app/platform/provenance/` | Sources/snapshots | EXISTING_VERIFIED | Claims & Evidence | UI not built |
| Platform claims | `backend/app/platform/claims/` | Claims | EXISTING_VERIFIED | Claims & Evidence | UI not built |
| Platform geo | `backend/app/platform/geo/` | Geo/jurisdiction | EXISTING_VERIFIED | Migration / Mobility (foundation) | UI not built |
| Platform lifecycle | `backend/app/platform/lifecycle/` | Goals and lifecycle kinds | EXISTING_VERIFIED | Platform Foundation | Goals via platform API |
| Platform privacy | `backend/app/platform/privacy/` | Privacy policies/consent | EXISTING_VERIFIED | Settings / Privacy | UI partial |
| Platform observability | `backend/app/platform/observability/` | Correlation/redaction/events | EXISTING_VERIFIED | infrastructure | |
| Agents job_search | `backend/app/agents/job_search/` | Job/interview-pack agent pipelines | EXISTING_NEEDS_REVIEW / FROZEN parts | Opportunities / legacy prep | 004E repair frozen |
| Agents cv_builder / roadmap / chatbot | `backend/app/agents/{cv_builder,roadmap,chatbot}/` | Domain agents | EXISTING_NEEDS_REVIEW | CV / Roadmaps / Assistant | |
| Agents auto_apply | `backend/app/agents/auto_apply/` | Legacy auto-apply | FROZEN | Applications (legacy) | Do not revive as Safe Apply |
| Schemas | `backend/app/schemas/*` | Pydantic contracts | EXISTING_VERIFIED | multi-domain | Includes `platform.py`, `career_subject.py` |
| Services | `backend/app/services/*` | Jobs discovery/dedupe/matching, badges, role packs | EXISTING_NEEDS_REVIEW | Opportunities / badges | |
| Tests | `backend/tests/`, `app/*/tests/`, `app/api/routes/tests/` | Unit/integration + platform tests | EXISTING_VERIFIED | multi-domain | |
| pyproject.toml | `backend/pyproject.toml` | Backend package config | EXISTING_VERIFIED | infrastructure | |
| requirements.txt | — | — | MISSING | infrastructure | Use pyproject; VERIFY_IN_REPO if elsewhere |

### 7.2 Current Frontend Module Inventory

| Frontend Area | Verified Path | Current Purpose | Current Status | Owned Domain | Notes |
|---|---|---|---|---|---|
| Routing entry | `frontend/src/App.tsx`, `main.tsx` | Public/Private routes + BrowserRouter | EXISTING_VERIFIED | shell | |
| Layout shell | `components/layout/{AppShell,Sidebar,Header}.*` | Auth chrome | EXISTING_VERIFIED | shell | |
| Shared UI | `components/ui/*` | Button/Card/Badge/Input/Modal/Spinner/Toast | EXISTING_VERIFIED | design system | |
| Feature components (jobs-heavy) | `components/features/*` | Job discovery/forms/filters; InterviewPackView; DefaultCVSelector; radar | EXISTING_NEEDS_REVIEW | Opportunities / legacy prep / CV helper | InterviewPackView ≠ Studio |
| Chatbot | `components/chatbot/*` | FAB widget | EXISTING_VERIFIED | AI Career Assistant | |
| Placeholder feature dirs | `components/{cvbuilder,dashboard,jobsearch,landing,profile,roadmap,settings}/` | Empty directories today | EXISTING_NEEDS_REVIEW | various | Present but empty — no giant rewrite; fill via slices |
| Pages | `pages/*` | Route screens including PlatformPage | EXISTING_VERIFIED | multi-domain | See UX0-S2 inventory |
| Styles / tokens | `styles/{globals,animations,feature-pages}.css` | Design tokens + utilities | EXISTING_VERIFIED | design system | |
| API client | `lib/api.ts` | Axios `/api/v1` + platformApi | EXISTING_VERIFIED | multi-domain | |
| API types | `types/api.ts` | TS contracts including platform | EXISTING_VERIFIED | multi-domain | |
| Store | `store/{auth,ui}.ts` | Auth + theme/toasts/sidebar | EXISTING_VERIFIED | shell | |
| Lib helpers (jobs) | `lib/job*.ts`, `lib/savedJob*.ts`, `lib/popularJobRoles*.ts` | Jobs UX logic | EXISTING_NEEDS_REVIEW | Opportunities / Jobs | |
| `features/` folder (target) | `frontend/src/features/` | — | MISSING | target structure | Planned incremental; do not rewrite now |
| Vite config | `frontend/vite.config.ts` | Build + `/api` proxy | EXISTING_VERIFIED | tooling | |

### 7.3 Product Domain Ownership Matrix

| Product Domain | User-Facing Pages | Backend Owner | Frontend Owner | Primary Models | Primary APIs | Current Status | MVP Slice |
|---|---|---|---|---|---|---|---|
| Platform Foundation | `/platform` | `app/platform/*` + `routes/platform.py` | `pages/PlatformPage.tsx` (later `features/platform/`) | career_subjects, career_goals (+ kernel) | `/api/v1/platform/*` | EXISTING_VERIFIED | PF11 done; PF11-R1 |
| Career Passport | `/passport*`, `/profile` (bridge) | planned `career_passport/` (+ profile today) | planned `features/passport/` + `pages/ProfilePage.tsx` | profile/education/experience (planned + existing profile models) | planned passport APIs; existing profile | PARTIAL_EXISTING | After 0052 |
| Claims & Evidence | Claims UI planned | `platform/claims`, `platform/provenance` | planned passport/claims UI | career_claims, provenance_* | foundation services; public CRUD limited | PARTIAL_EXISTING (BE) / PLANNED_MVP (UI) | After 0053 |
| CV Builder | `/cv-builder*` | `routes/cv_builder.py`, `agents/cv_builder`, models `cv.py` | `pages/CVBuilderPage.tsx`, `features/DefaultCVSelector` | CV versions/templates | `/api/v1` cv_builder routes | PARTIAL_EXISTING | CVB-F0–F5 |
| Roadmaps | `/roadmap`, planned `/roadmaps*` | `routes/roadmap.py`, `agents/roadmap`, models `roadmap.py` | `pages/RoadmapPage.tsx` | roadmaps, milestones/tasks | roadmap routes | PARTIAL_EXISTING | ROAD-F0–F4 |
| Opportunities / Jobs | `/jobs` | `routes/job_search.py`, `agents/job_search`, `services/job_*` | `pages/JobSearchPage.tsx`, `components/features/Job*` | saved_jobs | job-search APIs | PARTIAL_EXISTING | honesty baseline; 0054–55 later |
| Interview Studio | planned `/interview-studio*` | planned `interview_studio/` | planned `features/interview-studio/` | sessions/study (planned) | planned | FUTURE | After 0061 |
| Legacy Interview Pack | `/interview-pack` redirect; `InterviewPackView` | job_search interview-pack paths | InterviewPackView / JobSearch | pack artifacts | job-search pack endpoints | FROZEN | Do not repair 004E |
| Skills → Practice → Proof | planned `/skills`,`/practice`,`/proof` | planned `skills/` (+ claims) | planned `features/skills/` | skills, proof | planned | FUTURE | After 0060 |
| Applications / Safe Apply | planned `/applications*` | planned `applications/` | planned `features/applications/` | drafts/submissions | planned | FUTURE | After 0068 |
| Legacy Auto Apply | apply routes/agents | `routes/apply.py`, `agents/auto_apply` | — | apply models | apply APIs | FROZEN | Not Safe Apply |
| Education / Study Abroad | planned education hubs | planned `education/` | planned `features/education/` | education plans | planned | FUTURE | After 0069+ |
| Public Sector / Government | planned `/public-sector` | planned `public_sector/` | planned `features/public-sector/` | exams/sources | planned | FUTURE | After 0063+ |
| Migration / Mobility | planned `/migration` | planned `mobility/` + `platform/geo` | planned education/mobility UI | geo/jurisdiction | planned | FUTURE | After 0073 |
| Notifications | shell later | planned `notifications/` | layout later | notifications | planned | DEFERRED | 0074 |
| Billing | `/billing` | planned `billing/` | planned settings | subscriptions | planned | DEFERRED | 0075 |
| AI Career Assistant | `/chatbot`, FAB | `routes/chatbot.py`, `agents/chatbot` | chatbot components/pages | chat sessions/messages | chatbot APIs | PARTIAL_EXISTING | evolve; not autonomous agents |
| Settings / Privacy | `/settings` | profile + `platform/privacy` | `pages/SettingsPage.tsx` | user/profile/privacy | auth/profile | PARTIAL_EXISTING | privacy UI later |
| Admin / B2B Future | none | planned b2b | planned admin | orgs | planned | DEFERRED | 0076 |

### 7.4 Backend Target Ownership Rules

| Future Backend Module | Owns | Must Not Own | Reads From | Writes To | Security Rule | First Slice |
|---|---|---|---|---|---|---|
| `career_passport/` | Passport profile sections | Claims verification, CVs, roadmaps | identity subject, profile | passport tables | Owner checks | After 0052 |
| `cv_builder/` | CV versions/templates/export metadata | Claims verification; passport ownership | passport (read), skills (read) | CV tables only | Owner checks; export review | CVB-F4+ |
| `roadmaps/` | Roadmap plans/milestones/tasks | All Graduate Launch product logic | passport/skills (read), lifecycle goals (read) | roadmap tables | Owner checks | ROAD-F2+ |
| `opportunities/` | Source-backed opportunity/job intelligence records + fit analyses | Invented jobs/salaries/deadlines/company facts | passport/skills (read); job_search saved jobs (read) | opportunity/fit tables | Owner + source freshness | 0054–55 |
| `interview_studio/` | Interview sessions, study modules (new system) | Old 004E pack repair ownership | passport/skills/opportunity (read) | studio tables | Owner + source grounding | 0061 |
| `skills/` | Skills inventory, practice tasks, proof artifacts linkage | Unverified claim stamping | passport (read), claims/provenance (via contract) | skills/practice/proof | Owner + provenance for proof | 0060 |
| `applications/` | Drafts, review state, submissions, outcomes | Blind auto-apply / autonomous submit | CV + opportunity (read) | application tables | Owner + **human review gate** | 0068 |
| `education/` | Education/study-abroad plans | Fake program certainty | geo (read) | education tables | Owner + source freshness | 0069+ |
| `public_sector/` | Gov career/exam source records | Unsourced deadlines | geo (read) | public_sector tables | Owner + source freshness | 0063+ |
| `mobility/` | Migration pathway plans | Visa legal advice without sources | geo/education (read) | mobility tables | Owner + jurisdiction rules | 0073 |
| `billing/` | Subscriptions/entitlements | Core career data | user | billing tables | Owner + audit | 0075 |
| `notifications/` | Notification records/delivery state | Sensitive body logging | user prefs | notifications | Owner + consent | 0074 |
| `agent_orchestration/` | AI workflow orchestration / tool routing | Auth bypass; direct cross-domain writes; skipping human review | domain services (read via contracts) | orchestration logs only (redacted) | Never bypass permissions | Later, after deterministic workflows |

**Also:** Existing `app/platform/*` remains the foundation owner for subjects, goals, claims primitives, provenance, geo, privacy, observability. New modules must call platform services rather than reimplement kernel rules.

### 7.5 Frontend Target Ownership Rules

Current repo may not yet use `frontend/src/features/*`. Move toward it incrementally. Do not do a giant folder rewrite. Use existing `pages/` + `components/` until a dedicated refactor slice is approved.

| Future Frontend Feature Folder | Owns Pages | Owns Components | Depends On | Must Not Own | First Slice |
|---|---|---|---|---|---|
| `features/platform/` | `/platform` | Subject/goal UI | ui/, api platform methods | Claims/privacy UIs | PF11-R1 / later extract |
| `features/passport/` | `/passport*` | Passport sections | ui/, platform subject context | CV export logic | After 0052 |
| `features/cv-builder/` | `/cv-builder*` | Template gallery, preview, export UI | ui/, passport read | Claims verification | CVB-F1+ |
| `features/roadmaps/` | `/roadmaps*` | List/detail/tasks/timeline | ui/, platform goals read | Graduate-only ownership of all roadmaps | ROAD-F1+ |
| `features/opportunities/` | `/jobs*`, `/opportunities` | Job/opportunity cards/filters | ui/, jobs APIs | Fake certainty badges | Jobs stabilize → 0055 |
| `features/interview-studio/` | `/interview-studio*` | Session/practice/study UI | ui/ | 004E pack repair | After 0061 |
| `features/skills/` | `/skills`,`/practice`,`/proof` | Practice/proof UI | ui/, claims display contracts | Unverified “verified” stamps | After 0060 |
| `features/applications/` | `/applications*` | Tracker/drafts/Safe Apply review | ui/, CV + job read | Blind auto-apply UI | After 0068 |
| `features/education/` | education hubs | Info/checklist | ui/ | Unsourced advice | After 0069 |
| `features/public-sector/` | `/public-sector` | Gov navigator UI | ui/ | Fake deadlines | After 0063 |
| `features/settings/` | `/settings`,`/privacy`,`/billing` | Settings panels | ui/ | Billing before value | Privacy before 0075 |
| `features/assistant/` | chatbot/panel | Assistant panel | ui/, redacted context | Autonomous tool abuse | Evolve chatbot |

### 7.6 API Ownership Matrix

| API Group | Backend Module Owner | Frontend Caller | User-Owned Resource? | Auth Required? | Ownership Check Required? | Status |
|---|---|---|---|---|---|---|
| platform | `platform` + `routes/platform.py` | `platformApi` in `lib/api.ts` | Yes (subject/goal) | Yes | Yes | EXISTING_VERIFIED |
| career passport | planned `career_passport/` | planned passport client | Yes | Yes | Yes | PLANNED |
| claims/evidence | `platform/claims`, `platform/provenance` | planned | Yes | Yes | Yes | PARTIAL (BE) / PLANNED (FE) |
| cv builder | `routes/cv_builder` → future `cv_builder/` | CV pages / api | Yes | Yes | Yes | PARTIAL |
| roadmaps | `routes/roadmap` → future `roadmaps/` | Roadmap page / api | Yes | Yes | Yes | PARTIAL |
| opportunities/jobs | `job_search` (+ future `opportunities/`) | JobSearchPage / jobApi | Yes (saved jobs) | Yes | Yes | PARTIAL |
| interview studio | planned `interview_studio/` | planned | Yes | Yes | Yes | FUTURE |
| legacy interview pack | job_search pack endpoints | JobSearch / InterviewPackView | Yes | Yes | Yes | FROZEN expansion |
| skills/proof | planned `skills/` | planned | Yes | Yes | Yes (+ provenance) | FUTURE |
| applications/safe apply | planned `applications/` | planned | Yes | Yes | Yes + human review | FUTURE |
| legacy apply / auto apply | `routes/apply`, `agents/auto_apply` | VERIFY_IN_REPO FE usage | Yes | Yes | Yes | FROZEN |
| education | planned `education/` | planned | Yes | Yes | Yes | FUTURE |
| public sector | planned `public_sector/` | planned | Yes | Yes | Yes | FUTURE |
| migration/mobility | planned `mobility/` + geo | planned | Yes | Yes | Yes | FUTURE |
| notifications | planned `notifications/` | planned | Yes | Yes | Yes | DEFERRED |
| billing | planned `billing/` | planned | Yes | Yes | Yes | DEFERRED |
| assistant | chatbot routes/agents | chatbot UI | Yes | Yes | Yes | PARTIAL |

**Rules:** Every user-owned object route requires server-side ownership checks. No endpoint should trust user-controlled IDs. No high-impact AI output should bypass validation/human review.

### 7.7 Data Ownership Matrix

| Data Object | Backend Owner | Frontend Owner | Privacy Level | Provenance Needed? | User-Owned? | First Slice |
|---|---|---|---|---|---|---|
| career subject | platform/identity | platform UI | HIGH | No | Yes | PF11 |
| career goal | platform/lifecycle | platform UI | HIGH | Actor on create | Yes | PF11 |
| passport profile | career_passport (planned) / profile today | passport/profile UI | HIGH | Optional | Yes | 0052 |
| education record | career_passport / education | passport UI | HIGH | Optional | Yes | 0052 |
| experience record | career_passport | passport UI | HIGH | Optional | Yes | 0052 |
| project | career_passport | passport UI | MEDIUM | Optional | Yes | 0052 |
| skill | skills (planned) | skills/passport UI | MEDIUM | Optional | Yes | 0060 / 0052 |
| claim | platform/claims | claims UI | HIGH | Yes | Yes | 0053 |
| evidence/source snapshot | platform/provenance | claims UI | HIGH | Yes | Yes | 0053 |
| CV version | cv_builder | cv-builder UI | HIGH | Export lineage | Yes | CVB-F4 |
| CV template | cv_builder | cv-builder UI | LOW | No | Shared catalog | CVB-F2 |
| roadmap | roadmaps | roadmaps UI | MEDIUM | Optional | Yes | ROAD-F2 |
| roadmap milestone | roadmaps | roadmaps UI | MEDIUM | No | Yes | ROAD-F3 |
| roadmap task | roadmaps | roadmaps UI | MEDIUM | No | Yes | ROAD-F3 |
| saved job | job_search | jobs UI | MEDIUM | source_url | Yes | Existing |
| opportunity source record | opportunities (planned) | opportunities UI | MEDIUM | Yes | System+user | 0054 |
| opportunity fit analysis | opportunities | opportunities UI | MEDIUM | Yes | Yes | 0055 |
| interview session | interview_studio | studio UI | MEDIUM | Sources | Yes | 0061 |
| study module | interview_studio | studio UI | MEDIUM | Sources | Yes | 0061 |
| practice task | skills | skills UI | MEDIUM | No | Yes | 0060 |
| proof artifact | skills + claims | skills/proof UI | HIGH | Yes | Yes | 0060 |
| application draft | applications | applications UI | HIGH | No | Yes | 0068 |
| application submission | applications | applications UI | SENSITIVE | Yes | Yes | 0068 |
| outcome | applications / lifecycle | applications UI | MEDIUM | Optional | Yes | 0062/0068 |
| notification | notifications | shell | MEDIUM | No body dumps | Yes | 0074 |
| billing/subscription | billing | settings | SENSITIVE | Audit | Yes | 0075 |
| assistant context | chatbot / agent_orchestration | assistant UI | HIGH | Redact logs | Yes | Existing → evolve |

### 7.8 Cross-Domain Dependency Rules

- A module may read another domain only through a documented service/API contract.
- A module must not write another domain’s owned tables directly.
- Frontend feature pages should call their own feature API adapter or shared API client, not random cross-feature internals.
- Shared components must not contain domain-specific business logic.
- AI orchestration must request domain data through approved service contracts.
- Auth and privacy checks stay server-side.

**Examples:**

- CV Builder may read Career Passport data to prefill a CV, but must not own passport data.
- Roadmaps may read Skills and Passport data for personalization, but must own roadmap tasks.
- Opportunity Intelligence may read Passport and Skills, but must own fit analyses.
- Applications may read CV and Opportunity data, but must own drafts/submission state.
- Interview Studio may read Passport, Skills, and Opportunity context, but must own interview sessions and study modules.

### 7.9 Frozen / Deferred Domain Register

| Domain / System | Status | Reason | Replacement Direction | Allowed Action |
|---|---|---|---|---|
| Old 004E Interview Pack repair | FROZEN | Drift/cost; wrong product direction | Interview Studio (new) | Redirect/legacy only; no repair slices |
| Old Auto Apply | FROZEN | Unsafe agency | Safe Apply (0068) | Do not expand apply agents as product |
| Full autonomous agents | DEFERRED | Need deterministic workflows + checkpoints | Agent levels 0–2 first | ADR required |
| MCP external tool layer | DEFERRED | Core workflows not stable | Later integration | ADR required |
| Billing | DEFERRED | Core MVP value first | 0075 | Docs only until then |
| Admin / B2B | DEFERRED | Consumer MVP first | 0076 | Docs only |
| Migration/visa advisory depth | DEFERRED | Jurisdiction/source rules incomplete | 0073 with sources | No unsourced advice |
| Public-sector deadline automation | DEFERRED | Source freshness required | 0063–67 | No fake deadlines |

Frozen systems cannot be repaired opportunistically. Deferred systems require a future explicit slice and decision record.

### 7.10 Ownership Gate for Future Slices

Before any future implementation slice, the prompt must identify:

- product domain  
- backend owner  
- frontend owner  
- API owner  
- data owner  
- permission rule  
- privacy classification  
- provenance rule  
- tests  
- browser journey if user-visible  

If any are missing → **`BLOCKED_DOMAIN_OWNERSHIP_UNKNOWN`**.

### 7.11 UX0-S4 Implementation Decision

UX0-S4 is a **docs-only** domain ownership contract.

- No backend implementation is included in this slice.  
- No frontend implementation is included in this slice.  
- No folder restructuring or import moves are included in this slice.  
- Future domain implementation must happen through **explicit implementation slices after UX0-S5**.

---

## UX0-S5 Implementation Ladder Checkpoint

**Slice:** UX0-S5  
**Date:** 2026-07-11  
**Type:** Docs-only — closes UX0 planning and freezes immediate execution order  
**Companion cards:** Final PF11-R1…ROAD-F4 cards live in §43 (updated by this slice).

### 6.1 UX0 Planning Completion Summary

| Slice | Purpose | Status | Commit | Evidence | Notes |
|---|---|---|---|---|---|
| UX0-S1 | Master build plan + separate live tracker | Done | `563f9884` | `~/Desktop/CareerKundi_UX0_S1_Master_Plan_Live_Tracker_Evidence.txt` | Docs only |
| UX0-S2 | Navigation + sitemap contract | Done | `f9acda89` | `~/Desktop/CareerKundi_UX0_S2_Navigation_Sitemap_Evidence.txt` | Docs only |
| UX0-S3 | Design system + component inventory | Done | `258441c1` | `~/Desktop/CareerKundi_UX0_S3_Design_System_Component_Inventory_Evidence.txt` | Docs only |
| UX0-S4 | Backend/frontend domain ownership map | Done | `b803838c` | `~/Desktop/CareerKundi_UX0_S4_Domain_Ownership_Map_Evidence.txt` | Docs only |
| UX0-S5 | Implementation ladder checkpoint | Completing | Pending this slice | `~/Desktop/CareerKundi_UX0_S5_Implementation_Ladder_Checkpoint_Evidence.txt` | Docs only |

### 6.2 Transition Gate From UX Planning to Implementation

CareerKundi may move from UX0 planning into controlled implementation only when:

1. Master build plan exists  
2. Live tracker exists  
3. Navigation/sitemap contract exists  
4. Design system/component inventory exists  
5. Backend/frontend domain ownership map exists  
6. Implementation ladder checkpoint exists  
7. Live tracker identifies the exact next slice  
8. Repo is clean  
9. Latest commit is pushed  
10. Frozen/deferred systems remain protected  

If any item fails → **`BLOCKED_UX0_EXIT_GATE_INCOMPLETE`**.

### 6.3 Final Immediate Execution Order

Freeze this immediate order unless changed by a future decision record:

1. **PF11-R1** Platform Shell Review / Refinement  
2. **CVB-F0** CV Builder Audit  
3. **CVB-F1** CV Builder UI Repair  
4. **CVB-F2** CV Template Gallery + Preview  
5. **CVB-F3** CV PDF Export Verification  
6. **CVB-F4** CV Save/Load Versions  
7. **CVB-F5** CV Browser-Tested Checkpoint  
8. **ROAD-F0** Roadmap Audit  
9. **ROAD-F1** Roadmap UI Repair  
10. **ROAD-F2** Roadmap Save/Load Contract  
11. **ROAD-F3** Roadmap Detail + Task Tracking  
12. **ROAD-F4** Browser-Tested Checkpoint  
13. **UX checkpoint before 0051** (docs/evidence gate)  
14. **0051** Universal Role & Pathway Taxonomy  
15. **0052** Career & Education Passport  

**Rule:** Do not jump to 0051 until visible PF11 / CV Builder / Roadmap stabilization checkpoints are completed or explicitly deferred by decision record.

### 6.4 Slice Type Classification

| Slice | Type | Product Code Allowed? | Browser Journey Required? | Tests Required? | Commit Scope |
|---|---|---|---|---|---|
| PF11-R1 | AUDIT_ONLY (default); FRONTEND_VISIBLE if small approved refinement | Only if audit finds approved PF11-file fix | Yes | Build if code changed; docs checks always | Docs/evidence; optional PF11 UI files |
| CVB-F0 | AUDIT_ONLY | No | Open page (manual) | Manual audit notes | Docs/evidence only |
| CVB-F1 | FRONTEND_VISIBLE | Yes (CV UI files) | Load/edit/L/E/E | Frontend build | CV Builder FE |
| CVB-F2 | FRONTEND_VISIBLE | Yes | Template + preview | Frontend build | CV Builder FE |
| CVB-F3 | FRONTEND_VISIBLE or FULL_STACK | Yes (export path) | Export PDF | Build + PDF open | CV export FE/BE as needed |
| CVB-F4 | FULL_STACK if persistence missing | Yes | Save/refresh/load | API + UI ownership tests | CV versions API + FE |
| CVB-F5 | BROWSER_CHECKPOINT | Only if fix required | Full CV journey | Full risk-matched | Evidence (+ tiny fixes if needed) |
| ROAD-F0 | AUDIT_ONLY | No | Open page | Manual audit | Docs/evidence only |
| ROAD-F1 | FRONTEND_VISIBLE | Yes | List/empty/CTA | Frontend build | Roadmap FE |
| ROAD-F2 | FULL_STACK if persistence missing | Yes | Create/refresh | API + ownership tests | Roadmap API + FE |
| ROAD-F3 | FULL_STACK | Yes | Detail + task complete | API + UI | Roadmap detail/tasks |
| ROAD-F4 | BROWSER_CHECKPOINT | Only if fix required | Full roadmap journey | Full risk-matched | Evidence (+ tiny fixes if needed) |
| Pre-0051 UX checkpoint | ARCHITECTURE_GATE / DOCS_ONLY | No | No | Doc gate | Docs/tracker |
| 0051 | BACKEND_VISIBLE / ARCHITECTURE_GATE | Yes (taxonomy module) | N/A early | Migration + tests | Taxonomy backend |
| 0052 | FULL_STACK | Yes | Passport journey | Ownership + UI | Passport module + UI |

### 6.5 Next Slice Cards Finalization

The finalized cards for **PF11-R1 through ROAD-F4** are maintained in **§43 Detailed Technical Slice Cards** (expanded by UX0-S5). Each card includes: slice id, type, goal, allowed/forbidden files, backend/frontend/API/DB/AI/security tasks, tests, browser journey, evidence file, commit message, push rule, done definition.

Do not copy full cards into the live tracker.

### 6.6 Evidence Naming Convention

```text
~/Desktop/CareerKundi_<SLICE_ID>_<Short_Name>_Evidence.txt
```

Examples:

- `~/Desktop/CareerKundi_PF11_R1_Platform_Shell_Review_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F0_CV_Builder_Audit_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F1_UI_Repair_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F2_Template_Preview_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F3_PDF_Export_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F4_Save_Load_Evidence.txt`
- `~/Desktop/CareerKundi_CVB_F5_Browser_Checkpoint_Evidence.txt`
- `~/Desktop/CareerKundi_ROAD_F0_Roadmap_Audit_Evidence.txt`
- `~/Desktop/CareerKundi_ROAD_F1_UI_Repair_Evidence.txt`
- `~/Desktop/CareerKundi_ROAD_F2_Save_Load_Contract_Evidence.txt`
- `~/Desktop/CareerKundi_ROAD_F3_Detail_Task_Tracking_Evidence.txt`
- `~/Desktop/CareerKundi_ROAD_F4_Browser_Checkpoint_Evidence.txt`

### 6.7 Commit Message Convention

```text
docs(product): <docs-only planning work>
docs(product): record <audit/checkpoint>
feat(frontend): <frontend visible feature>
feat(<domain>): <full-stack/backend domain feature>
test(<domain>): <test/checkpoint work>
fix(<domain>): <bug fix within approved slice>
```

Rules:

- One slice per commit where possible.  
- Do not mix audit docs with product implementation unless explicitly approved.  
- Do not commit generated build output.  
- Do not use broad `git add`.  
- Every accepted slice updates the live tracker.  
- Master plan updates only when architecture / ladder / slice cards change.

### 6.8 Implementation Acceptance Gate

Every implementation slice must pass:

1. Allowed files respected  
2. Forbidden files untouched  
3. Live tracker updated  
4. Tests matched risk  
5. Browser journey completed if user-visible  
6. `frontend/dist` ignored if frontend build ran  
7. Security/privacy reviewed if user data touched  
8. No frozen systems touched  
9. Evidence file created  
10. Commit/push verified if required  

If any item fails, use **`NEEDS_FIX`**, **`BLOCKED`**, or **`REJECTED`** — do not mark **`PASS_ACCEPTED`**.

### 6.9 First Post-UX0 Slice Decision

After UX0-S5, the next slice is:

**PF11-R1 — Platform Shell Review / Refinement**

**Reason:** PF11 created the first authenticated Platform shell. Before stabilizing CV Builder and Roadmaps, the Platform shell should be reviewed against the completed UX0 navigation, design system, and domain ownership contracts.

**PF11-R1 default behavior:**

- Start as **AUDIT_ONLY**.  
- Do not modify product code unless the audit finds a small approved refinement inside PF11 allowed files.  
- If no refinement is needed, commit only docs / live tracker / evidence.  
- If refinement is needed, product-code change requires exact allowed files, browser journey, build check, and tracker update.

### 6.10 UX0-S5 Implementation Decision

UX0-S5 is a **docs-only** implementation ladder checkpoint.

- No backend implementation is included in this slice.  
- No frontend implementation is included in this slice.  
- This slice **closes UX0 planning** and prepares **PF11-R1** as the next controlled execution slice.

---

## PF11-R1 Platform Shell Review / Refinement Audit

**Slice type:** AUDIT_ONLY (no product-code changes in PF11-R1).  
**Inspected (read-only):** `App.tsx`, `Sidebar.tsx`, `Header.tsx`, `PlatformPage.tsx`, `lib/api.ts` (`platformApi`), `types/api.ts` (Platform* types).  
**Evidence:** `~/Desktop/CareerKundi_PF11_R1_Platform_Shell_Review_Evidence.txt`

### 7.1 Audit Summary Table

| Area | Result | Evidence | Notes | Follow-up |
|---|---|---|---|---|
| Route placement | PASS | `App.tsx` `/platform` under `PrivateRoute` + `AppShell` | Auth-gated; Career Core foundation shell; not a full dashboard/passport/claims system | None for PF11 |
| Sidebar/navigation fit | PARTIAL | `Sidebar.tsx` Career Tools → Platform | Platform visible; no Interview Pack / Auto Apply nav revival. Stale file comment still mentions Interview Pack. Group label still **Career Tools** vs UX0-S2 target **Career Core** | Deferred nav remap slice (already decided in UX0-S2); not PF11-R2 |
| Header/breadcrumb fit | PASS | `Header.tsx` `PAGE_LABELS.platform` = "Platform Foundation" | Aligns with UX0-S2 breadcrumb for `/platform`. `chatbot` still lacks explicit label (falls back to segment text) | Future Header cleanup; not PF11-R2 |
| Platform page product scope | PASS | `PlatformPage.tsx` subjects + goals only | Explicit “Foundation preview” + status card stating claims/evidence/recommendations/privacy/opportunities come later | None |
| Design system fit | PASS | Button, Card, Input/Textarea, Spinner, toasts | Loading / empty / error / visible create actions present; consistent with existing shell; no giant visual rewrite | Optional polish later |
| Domain ownership fit | PASS | `platformApi` + Platform* types only | Does not own CV Builder, Roadmaps, Passport, Claims, or Opportunities UIs | None |
| Browser journey | BLOCKED_BROWSER_SETUP | Local Vite not running; no authenticated test session in this slice | Required journey not claimed. API probe: `GET /api/v1/platform/subjects` → **401** without auth (gate present) | Re-verify during later browser checkpoints if desired; does **not** block next slice |
| Console/network health | VERIFY_IN_REPO | Not observed in a live browser session | Static review only | Optional browser re-check |

### 7.2 PF11-R1 Decision

**B PF11_PLATFORM_SHELL_ACCEPTED_WITH_MINOR_FOLLOW_UP**

Rationale: `/platform` is correctly auth-gated, scoped to subjects/goals, uses shared UI primitives and platform domain APIs, and does not revive frozen 004E / Auto Apply surfaces. Remaining gaps are known deferred nav/breadcrumb cleanups outside PF11 product files — not shell defects requiring PF11-R2 code changes.

### 7.3 Recommended Next Slice

**Next slice: CVB-F0 CV Builder Audit**

(Decision B → continue immediate ladder; do **not** insert PF11-R2.)

### 7.4 PF11-R2 Recommendation

**PF11-R2 not required.**

No product-code refinement slice is recommended from this audit. If a future decision wants platform shell polish (e.g. friendlier subject labels), open an explicit slice with allowed files — do not invent PF11-R2 from this review.

**Deferred (non-PF11) follow-ups already on the plan:**

1. Sidebar remap Main/Career Tools/… → UX0-S2 groups (Career Core, Build, Roadmaps, …)  
2. Expand `PAGE_LABELS` for `chatbot` (and other unlabeled segments)  
3. Stale Sidebar header comment mentioning Interview Pack  

### 7.5 PF11-R1 Implementation Decision

PF11-R1 is **AUDIT_ONLY**.

- No frontend product-code changes.  
- No backend product-code changes.  
- Platform shell accepted for ladder progression to **CVB-F0**.  
- Frozen systems remain protected (old 004E Interview Pack repair; old Auto Apply).

---

## CVB-F0 CV Builder Audit

**Slice type:** AUDIT_ONLY (no product-code changes in CVB-F0).  
**Inspected (read-only):** `App.tsx` route, `pages/CVBuilderPage.tsx`, `features/DefaultCVSelector.tsx`, `lib/api.ts` (`cvApi`), `types/api.ts` (`GeneratedCVRead`), `styles/feature-pages.css` (`.cv-studio*`), `backend/app/api/routes/cv_builder.py`, `schemas/cv_builder.py`, `db/models/cv.py`, `agents/cv_builder/*`, `tools/document_export.py`, `main.py` router include.  
**Evidence:** `~/Desktop/CareerKundi_CVB_F0_CV_Builder_Audit_Evidence.txt`  
**Search terms:** `cv-builder`, `CV Builder`, `CvBuilder`, `resume`, `template`, `pdf`, `export`, `cv_builder`, `GeneratedCV`

### 8.1 Current CV Builder Route Inventory

| Route | Page / Component | Access | Current Status | Source File | Notes |
|---|---|---|---|---|---|
| `/cv-builder` | `CVBuilderPage` | Auth + `AppShell` | EXISTING_VERIFIED | `frontend/src/pages/CVBuilderPage.tsx` | Single studio route; sidebar Career Tools → CV Builder; breadcrumb `PAGE_LABELS["cv-builder"]` |
| `/cv-builder?jobId=` | same | Auth | EXISTING_VERIFIED | `CVBuilderPage` `useSearchParams` | Prefills target job when jobs list loads |
| `/cv-builder/templates` | — | — | PLANNED | — | Not a separate route; gallery is in-page |
| `/cv-builder/editor` | — | — | PLANNED | — | Editing is in-page sidebar + profile link |
| `/cv-builder/preview` | — | — | PLANNED | — | In-page `cv-studio__viewer` |
| `/cv-builder/export` | — | — | PLANNED | — | In-page PDF/DOCX/MD buttons → API export |

### 8.2 Current Frontend CV Builder Inventory

| Area | Verified File / Component | Current Behavior | Status | Notes |
|---|---|---|---|---|
| Page component | `pages/CVBuilderPage.tsx` | Full “AI CV Studio” layout (sidebar + viewer) | EXISTING_VERIFIED | Large single file; builds successfully (`CVBuilderPage-*.js` chunk) |
| Related component | `features/DefaultCVSelector.tsx` | Default CV picker for applications (`localStorage` key `ck_default_cv_id`) | EXISTING_VERIFIED | Used outside builder (jobs/apply flows) |
| Form sections | Section toggles + reorder; CV name; tone; target job import; role-targeted mode | Toggle/reorder 12 section kinds; content sourced from profile or AI generate | EXISTING_NEEDS_REVIEW | Not a free-form CV editor; profile edits via `/profile` link |
| Template selection | In-page gallery of **12** tiles | Sets FE `selectedTemplate`; maps to **4** backend templates (`modern`/`classic`/`compact`/`creative`) | EXISTING_NEEDS_REVIEW | Gallery exists; visual fidelity vs export is F2/F3 risk |
| Preview | `ProfileCVPreview` / `RenderedCVPreview` | Live profile preview before generate; rendered snapshot after generate; visual/ATS + viewport modes | EXISTING_NEEDS_REVIEW | Preview accent/fonts change with FE template; export uses backend template id |
| PDF/export action | `cvApi.downloadPdf` via PDF/DOCX/MD buttons | Downloads blob with filename from CV name | EXISTING_NEEDS_REVIEW | Requires existing/generated `cvId`; toast if none |
| Save/load behavior | Generate persists; list + Load; default star in `localStorage` | `POST /generate` saves; `GET /` lists; Load calls `cvApi.get` | EXISTING_NEEDS_REVIEW | No in-UI delete/regenerate; no PATCH edit of rendered content |
| API calls | `cvApi`, `profileApi`, `jobApi` | list/get/generate/downloadPdf; profile + saved jobs | EXISTING_VERIFIED | FE does not call regenerate/delete/improve-bullet |
| Types | `GeneratedCVRead` in `types/api.ts` | Matches backend `CVRead` shape | EXISTING_VERIFIED | |
| Loading state | Generate overlay + button `loading` | Generate pending shows overlay/skeleton | EXISTING_NEEDS_REVIEW | Profile/jobs/cvs queries lack dedicated loading UI |
| Empty state | Saved library “No CVs yet”; empty preview copy | Present for library + empty profile sections | EXISTING_NEEDS_REVIEW | |
| Error state | Toasts on generate/export failure | Query `isError` for profile/cvs/jobs not surfaced in-page | EXISTING_NEEDS_REVIEW | Primary F1 gap |
| Success state | Toast on generate/load/default | Present | EXISTING_VERIFIED | |
| Mobile/responsive | `.cv-studio` CSS `@media (max-width: 1024px)` | Stacks to single column; sidebar `max-height: 50vh` | EXISTING_NEEDS_REVIEW | Browser/mobile UX VERIFY_IN_REPO |

### 8.3 Current Backend CV Builder Inventory

| Backend Area | Verified File / Endpoint | Current Behavior | Status | Notes |
|---|---|---|---|---|
| Routes | `api/routes/cv_builder.py` prefix `/cv-builder` | generate, list, get, delete, regenerate, export, improve-bullet | EXISTING_VERIFIED | Mounted in `main.py` under `/api/v1` |
| Schemas | `schemas/cv_builder.py` | `CVGenerateRequest`, `CVRead`, bullet improve contracts | EXISTING_VERIFIED | Backend templates Literal: modern/classic/compact/creative |
| Services / agents | `agents/cv_builder/{graph,agents,render,state,mock_data}.py` | Multi-agent generate + bullet improve; deterministic `render_cv` | EXISTING_VERIFIED | AI path is out of F1 scope |
| Models/storage | `db/models/cv.py` `GeneratedCV` / `generated_cvs` | Persists name, template, section_config, rendered_content snapshot | EXISTING_VERIFIED | User-owned rows |
| PDF/export logic | `tools/document_export.py` + `GET /{cv_id}/export` | Deterministic PDF/DOCX/Markdown; filename from CV name | EXISTING_VERIFIED | No LLM on export |
| Auth/ownership | `_get_owned_cv`, `_get_owned_target_job`, `get_current_user` | 401 without auth (probed); NotFound if not owner | EXISTING_VERIFIED | API probe: `GET /api/v1/cv-builder/` → **401** |
| Tests | Dedicated CV Builder route/agent tests | Not found under `backend/**/test*.py` for cv_builder | MISSING | VERIFY_IN_REPO if tests live under alternate names |

### 8.4 Current CV Builder Capability Matrix

| Capability | Current Status | Evidence | Gap | Target Slice |
|---|---|---|---|---|
| route exists | Yes | `App.tsx` `/cv-builder` | None | — |
| page loads | Likely (build OK) | Frontend build emits `CVBuilderPage` chunk | Browser not verified | CVB-F1 / CVB-F5 |
| editable CV sections | Partial | Toggles/reorder + profile link; not inline CV field editor | Clarify UX; surface L/E/E | CVB-F1 |
| template gallery | Partial | 12 FE tiles present | Map/clarify vs 4 BE templates; fidelity | CVB-F2 |
| template preview | Partial | Live FE preview | Preview may not match export layout | CVB-F2 |
| ATS-friendly template | Partial | FE `category: "ats"` tiles + ATS preview mode | Backend compact/classic mapping only | CVB-F2 |
| modern visual template | Partial | FE visual tiles → modern/creative/classic | Same mapping gap | CVB-F2 |
| PDF export | Partial | Route + FE buttons + `export_pdf` | Reliability/browser verify | CVB-F3 |
| safe filename | Partial | Spaces → `_` in FE and BE | Edge chars VERIFY_IN_REPO | CVB-F3 |
| save CV version | Partial | Generate creates `GeneratedCV` | No explicit version naming/history UX | CVB-F4 |
| load CV version | Partial | Library Load + `cvApi.get` | No delete UI; regenerate unused | CVB-F4 |
| auth/ownership protection | Yes | Depends + ownership helpers; 401 probe | — | — |
| loading/empty/error states | Partial | Generate L; library empty; weak query error UI | Add profile/cvs/jobs L/E/E | CVB-F1 |
| mobile usability | Partial | CSS breakpoint | Browser verify | CVB-F1 / CVB-F5 |
| browser journey verified | No | Vite down this slice | `BLOCKED_BROWSER_SETUP` | CVB-F5 (and F1 smoke if available) |

### 8.5 Gap Analysis Against Master Plan

**Already exists**

- Authenticated `/cv-builder` studio page with sidebar controls and live preview.  
- Backend generate/list/get/delete/regenerate/export + ownership.  
- Persistence via `generated_cvs`.  
- Template gallery UI (12), ATS/visual preview modes, export buttons, saved library + default CV localStorage.  
- Profile-driven preview before AI generate.

**Partially present**

- Templates: FE 12 → BE 4 (preview accents ≠ distinct export templates).  
- Save/load: generate/list/load work; delete/regenerate APIs unused in UI.  
- L/E/E: generate covered; list/profile/jobs query failures not.  
- Nested routes from UX0 sitemap remain PLANNED (in-page today is acceptable for MVP).

**Broken or risky (documented, not fixed here)**

- Preview/export template mismatch risk.  
- AI generate/export reliability unverified in browser.  
- Missing dedicated automated CV Builder tests (search found none).  
- Unused FE imports / dead API surface (e.g. regenerate) are hygiene risks for F1.

**Missing (do not invent as existing)**

- Separate `/cv-builder/templates|editor|preview|export` routes.  
- Cover letters / portfolio (explicitly not MVP).  
- Passport-owned CV data (CV may read profile only).

**Must not be built yet**

- Passport/claims ownership of CV content.  
- AI rewrite expansion beyond existing generate (F1 forbids advanced AI work).  
- Safe Apply / Auto Apply coupling expansion.  
- Broad visual redesign.

**Next repair slice focus (CVB-F1)**

- Ensure `/cv-builder` loads cleanly with usable controls.  
- Add/fix loading, empty, and error states for profile / CV list / jobs queries.  
- Fix any import/type/console issues discovered during F1.  
- Do **not** expand template gallery, PDF hardening, or save/load product scope (F2–F4).

### 8.6 CV Builder Risk Register

| Risk | Impact | Evidence | Recommended Handling | Target Slice |
|---|---|---|---|---|
| Route/page crash | High | Not observed in build; browser unverified | Smoke load + fix crashes only | CVB-F1 |
| Broken imports/types | Medium | Build passes; unused `Download` import noted | Clean only if F1 touches file | CVB-F1 |
| Incomplete form structure | Medium | Sections are toggles, not inline editors | Document; keep profile-link pattern unless F1 needs clarity | CVB-F1 |
| Template selection missing | Low | Gallery exists | Stabilize mapping/preview | CVB-F2 |
| Preview/export mismatch | High | 12 FE vs 4 BE templates | Align preview semantics with export | CVB-F2 / CVB-F3 |
| PDF export not reliable | High | Code path exists; browser unverified | Verify formats + safe filename | CVB-F3 |
| CV data not persisted | Low | `GeneratedCV` + generate persist | Improve load/delete UX | CVB-F4 |
| No ownership checks | Low (mitigated) | `_get_owned_cv` + 401 probe | Keep; regression tests later | CVB-F4 / tests |
| Browser journey not verified | Medium | Vite down; no auth session | F1 smoke if possible; full journey F5 | CVB-F5 |
| Console/network errors | Medium | VERIFY_IN_REPO | Capture in F1 browser if available | CVB-F1 |
| Mobile layout problems | Medium | CSS stacks; 50vh sidebar | Verify + small CSS only if broken | CVB-F1 / F5 |
| Missing automated tests | Medium | No cv_builder test hits found | Add when stabilizing F3/F4 | Later |

### 8.7 CVB-F1 Repair Scope Recommendation

**CVB-F1 should focus only on:**

1. Making `/cv-builder` load cleanly under auth.  
2. Repairing current UI crashes / import / type issues if found.  
3. Making existing form/sidebar controls usable (name, sections, tone, job import, generate button affordances).  
4. Adding or documenting loading / empty / error states for profile, CV list, and jobs queries.  
5. Ensuring no console errors in the basic load journey (when browser available).  
6. Updating live tracker + evidence.

**CVB-F1 should not include:**

- Template gallery expansion or redesign (CVB-F2)  
- PDF export stabilization (CVB-F3)  
- Save/load persistence product work beyond what’s needed for page usability (CVB-F4)  
- AI CV rewriting / pipeline changes  
- Backend migrations unless the route is unusable without them  
- Large visual redesign  

**Suggested allowed files for CVB-F1 (finalize in F1 prompt):**

- `frontend/src/pages/CVBuilderPage.tsx`  
- `frontend/src/styles/feature-pages.css` (CV studio selectors only if needed)  
- Docs/tracker only besides the above  

### 8.8 CVB-F0 Decision

**A CV_BUILDER_READY_FOR_CVB_F1_UI_REPAIR**

Rationale: `/cv-builder` and backend CV APIs exist and compile; capability gaps are documented for F1–F5. Browser was unavailable this slice but does **not** block starting F1 UI repair (mark journey `BLOCKED_BROWSER_SETUP` for verification only).

**Recommended next slice:** **CVB-F1 CV Builder UI Repair**

### 8.9 CVB-F0 Audit-Only Decision

CVB-F0 is **audit-only**.

- No CV Builder product code was modified.  
- No backend product code was modified.  
- Any repair must happen in **CVB-F1** or later.  
- Frozen systems remain protected (old 004E Interview Pack repair; old Auto Apply).

---

## CVB-F1 CV Builder UI Repair

**Slice type:** FRONTEND_VISIBLE  
**Evidence:** `~/Desktop/CareerKundi_CVB_F1_UI_Repair_Evidence.txt`

### 11.1 Repair Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| page load | Studio rendered; weak workspace feedback | Workspace status strip + cleaner draft copy | PASS (build) | Browser not run |
| profile query state | `data` only | Loading / error + Retry / thin-profile empty CTA | PASS | |
| saved CVs query state | Empty “No CVs yet” only | Loading spinner, error, clearer empty | PASS | |
| jobs query state | Silent empty select | Loading / empty copy; disable select on load/error | PASS | |
| empty states | Minimal | Profile thin + jobs empty + CV library empty | PASS | Action-oriented |
| error states | Generate/export toasts only | Query errors + loadCV try/catch + Retry | PASS | |
| disabled/submitting states | Generate/export loading only | Disable generate when profile loading/error; disable export without draft; Load button loading | PASS | |
| visual consistency | Existing studio CSS | Small `.cv-studio__status*` styles only | PASS | No redesign |
| build result | Previously passing | `npm run build` (tsc + vite) PASS | PASS | |
| browser journey | Blocked in F0 | Not run this slice | BLOCKED_BROWSER_SETUP | Vite down; no auth session |

### 11.2 Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/CVBuilderPage.tsx` | Repair | L/E/E, honest draft copy, safe disabled states, unused import cleanup | Allowed |
| `frontend/src/components/features/DefaultCVSelector.tsx` | Repair | Loading/empty/error for CV list selector | Allowed |
| `frontend/src/styles/feature-pages.css` | Repair | Status row styles for CV studio | Allowed |
| `docs/product/careerkundi_master_build_plan.md` | Docs | F1 outcome section | Allowed |
| `docs/product/careerkundi_live_tracker.md` | Docs | Progress + next = F2 | Allowed |

`frontend/src/lib/api.ts` / `types/api.ts`: **not modified**.

### 11.3 Remaining CV Builder Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Template Gallery + Preview | CVB-F2 | Align FE accents with export templates; preview fidelity |
| PDF Export Verification | CVB-F3 | Reliability, formats, safe filename |
| Save/Load Versions | CVB-F4 | Library UX (delete/regenerate), version clarity |
| Browser-Tested Checkpoint | CVB-F5 | Full authenticated journey + console/network |

### 11.4 CVB-F1 Decision

**B CVB_F1_UI_REPAIR_ACCEPTED_BROWSER_SETUP_BLOCKED**

Rationale: UI repair for workspace L/E/E and honest draft language is in place and builds cleanly. Authenticated browser journey was not available this slice; does **not** require F1B before F2.

### 11.5 Recommended Next Slice

**Next slice: CVB-F2 CV Template Gallery + Preview**

---

## CVB-F2 CV Builder Studio Redesign + 15-Template Gallery + Live Preview Engine

**Slice type:** FRONTEND_VISIBLE  
**Evidence:** `~/Desktop/CareerKundi_CVB_F2_Template_Preview_Evidence.txt`

### 12.1 Delivery Summary

| Area | Result | Notes |
|---|---|---|
| Studio redesign | PASS | Layered header + gallery + live preview + right panel |
| 15-template catalog | PASS | Frontend registry in `CVTemplateGallery.tsx` |
| Gallery shows all 15 | PASS | Catalog length = 15 |
| Selected template updates preview | PASS | State-driven `CVTemplatePreview` |
| Structurally distinct layouts | PASS | Sidebar / editorial / matrix / ATS / metric / blueprint / etc. |
| Template metadata in UI | PASS | Name, category, best-for, ATS, strengths in panel |
| Honest actions | PASS | Preview / Save Draft / Export PDF (no false completeness) |
| Scope exclusions | PASS | No PDF harden, no version persistence product, no AI rewrite, no backend |
| Generated image assets | NO | CSS/React only |
| Build | PASS | `npm run build` |
| Browser journey | BLOCKED_BROWSER_SETUP | Vite down |

### 12.2 Files Changed

| File | Change Type | Reason |
|---|---|---|
| `frontend/src/pages/CVBuilderPage.tsx` | Redesign | Studio shell wiring |
| `frontend/src/components/features/CVTemplateGallery.tsx` | New | Catalog + gallery |
| `frontend/src/components/features/CVTemplatePreview.tsx` | New | Live preview engine |
| `frontend/src/components/features/CVBuilderStudioPanel.tsx` | New | Content/style + metadata panel |
| `frontend/src/styles/feature-pages.css` | Extend | Scoped `.cv-builder-studio*` / `.cv-template-*` styles |
| `docs/product/careerkundi_master_build_plan.md` | Docs | F2 outcome |
| `docs/product/careerkundi_live_tracker.md` | Docs | Progress → F3 |

### 12.3 Remaining CV Builder Work

| Remaining Work | Target Slice |
|---|---|
| PDF Export Verification | CVB-F3 |
| Save/Load Versions | CVB-F4 |
| Browser-Tested Checkpoint | CVB-F5 |

### 12.4 CVB-F2 Decision

**B CVB_F2_15_TEMPLATE_GALLERY_ACCEPTED_BROWSER_SETUP_BLOCKED**

### 12.5 Recommended Next Slice

**Next slice: CVB-F3 CV PDF Export Verification**

---

## CVB-F3 CV PDF Export Verification

**Slice type:** FRONTEND_VISIBLE + small FULL_STACK export fix  
**Evidence:** `~/Desktop/CareerKundi_CVB_F3_PDF_Export_Evidence.txt`

### 14.1 Export Flow Summary

| Area | Before | Change / Verification | Result | Notes |
|---|---|---|---|---|
| Export button | Present; basic blob download | Loading copy, disabled guard, tooltip | PASS | |
| Selected template propagation | Export ignored gallery selection | `template_id` query + FE `downloadPdf(..., { templateId })` | PASS | Maps to 4 PDF CSS families |
| Safe filename | `Name.pdf` loose | `CareerKundi_<Name>_<Template>_CV.pdf` FE+BE | PASS | Sanitized tokens |
| Frontend export state | Toast only | exportError / exportSuccess / Exporting… | PASS | |
| Backend export route | `GET /cv-builder/{id}/export` | Optional `template_id`; ownership unchanged | PASS | |
| Ownership/auth check | `_get_owned_cv` + `get_current_user` | Unchanged | PASS | |
| PDF response | `application/pdf` bytes | Unchanged media type + safer Content-Disposition | PASS | |
| Error handling | Generic toast | User-readable FE errors; unknown template → 422 | PASS | |
| Build | — | Frontend build PASS | PASS | |
| Browser journey | — | Not run | BLOCKED_BROWSER_SETUP | |

### 14.2 Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/CVBuilderPage.tsx` | Update | Export states, safe filename, templateId | Allowed |
| `frontend/src/lib/api.ts` | Update | `downloadPdf` optional `templateId` | Allowed |
| `frontend/src/components/features/CVBuilderStudioPanel.tsx` | Update | Honest PDF mapping footnote | Allowed |
| `frontend/src/styles/feature-pages.css` | Update | `.cv-builder-export*` status styles | Allowed |
| `backend/app/tools/document_export.py` | Update | resolve style + safe filename helpers | Allowed |
| `backend/app/api/routes/cv_builder.py` | Update | `template_id` query + safe filename header | Allowed |
| `backend/tests/unit/test_document_export.py` | Test | Style resolve + filename tests | Allowed |
| docs master + live tracker | Docs | F3 outcome | Allowed |

### 14.3 Export Capability Decision

**SELECTED_TEMPLATE_ID_WIRED_BUT_RUNTIME_BROWSER_BLOCKED**

Studio `template_id` is accepted and mapped to PDF CSS families (`modern|classic|compact|creative`). Full 15-layout PDF parity remains deferred. Authenticated browser download not verified this slice.

### 14.4 Remaining CV Builder Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Save/Load Versions | CVB-F4 | Persistence UX |
| Browser-Tested Checkpoint | CVB-F5 | Full export journey |
| Template-specific PDF layout parity (beyond 4 CSS families) | Future approved slice / CVB-F3B | Documented limitation |
| AI CV rewriting | Future AI slice | Out of scope |
| More templates beyond 15 | Future approved slice | Out of scope |

### 14.5 CVB-F3 Decision

**B CVB_F3_ACCEPTED_BROWSER_SETUP_BLOCKED**

### 14.6 Recommended Next Slice

**Next slice: CVB-F4 CV Save/Load Versions**

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
| CVB-F4 | Save/Load Versions | Persist CVs | After F3 | PATCH + section_config meta | Save/load UI | No | None | Ownership | API+UI tests | Save/refresh/load | CVB-F4 | Yes | Existing APIs | CV+API | Yes | Done (Decision B) |
| CVB-F5 | CV Browser Checkpoint | Close CVB | After F3+F4 | — | — | — | — | — | Full | Full CV journey | CVB-F5 | Yes | No | evidence/docs | Yes | Done (Decision B) |
| ROAD-F0 | Roadmap Audit | Audit only | Before repair | Inspect | Inspect | None | None | — | Manual | Open page | ROAD-F0 | Yes | No | docs | Optional | Done (Decision A) |
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
- **Type:** DOCS_ONLY / ARCHITECTURE_GATE  
- **Goal:** Freeze next execution order, evidence/commit conventions, and UX0 exit gate.  
- **Allowed:** `docs/product/careerkundi_master_build_plan.md`, `docs/product/careerkundi_live_tracker.md`  
- **Forbidden:** All product code; migrations; UI redesign; frozen 004E / Auto Apply  
- **Backend/Frontend/API/DB/AI:** None  
- **Security/privacy:** Protect frozen systems in tracker  
- **Tests:** Doc section greps + git scope  
- **Browser:** No  
- **Evidence:** `~/Desktop/CareerKundi_UX0_S5_Implementation_Ladder_Checkpoint_Evidence.txt`  
- **Commit message:** `docs(product): checkpoint implementation ladder`  
- **Push:** Yes after verification  
- **Done definition:** Exit gate documented; order frozen; next slice = PF11-R1; tracker updated  

### PF11-R1 — Platform Shell Review / Refinement
- **Type:** AUDIT_ONLY (default); FRONTEND_VISIBLE only if small approved refinement  
- **Goal:** Review committed `/platform` against UX0 nav, design, and ownership contracts.  
- **Allowed (audit):** docs/tracker + read-only inspect of Platform route/page/nav/header/api types.  
- **Allowed (refinement only if approved):** `frontend/src/pages/PlatformPage.tsx` and only other PF11 files explicitly listed in the PF11-R1 prompt.  
- **Forbidden:** Claims/privacy/geo UI; job_search; foundation_migrations; `frontend/dist`; Auto Apply; 004E repair; broad sidebar redesign.  
- **Backend tasks:** None unless API contract mismatch proven (tiny fix only).  
- **Frontend tasks:** Inspect route, sidebar placement, breadcrumb, layout, subjects/goals only, L/E/E states.  
- **API/DB/AI:** Inspect platform subjects/goals envelopes; no migration; no AI.  
- **Security/privacy:** Auth required; ownership already server-side; no auth bypass.  
- **Tests:** Frontend build if code changed.  
- **Browser journey:** login → `/platform` → list/create subject → create goal → refresh persist; console clean.  
- **Evidence:** `~/Desktop/CareerKundi_PF11_R1_Platform_Shell_Review_Evidence.txt`  
- **Commit message:** `docs(product): record PF11 platform shell review` or `fix(frontend): refine platform foundation shell`  
- **Push:** Yes if committed  
- **Done definition:** Review complete; subjects/goals-only confirmed; refinement either not needed or verified with journey  
- **PF11-R1 outcome (2026-07-12):** Decision **B** — accepted with minor follow-up; **no PF11-R2**; next = **CVB-F0**. Full audit in master § PF11-R1 Platform Shell Review / Refinement Audit.

### CVB-F0 — CV Builder Audit
- **Type:** AUDIT_ONLY  
- **Goal:** Document current CV Builder routes/components/APIs/PDF/export and define F1–F5 precisely.  
- **Allowed:** Docs/tracker/evidence; read-only inspect CV pages/components/API/types.  
- **Forbidden:** Product code changes; AI rewrite features; folder rewrite.  
- **Backend/Frontend/API/DB/AI:** Inspect only.  
- **Security/privacy:** Note ownership assumptions.  
- **Tests:** Manual page open notes.  
- **Browser:** Open `/cv-builder` and record behavior (not a pass/fail product fix).  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F0_CV_Builder_Audit_Evidence.txt`  
- **Commit message:** `docs(product): record CV Builder audit`  
- **Push:** Optional/yes after verification  
- **Done definition:** Broken behaviors listed; F1–F5 scoped; no code changes  
- **Product code allowed:** No  
- **CVB-F0 outcome (2026-07-12):** Decision **A** — ready for CVB-F1 UI repair. Full audit in master § CVB-F0 CV Builder Audit. Browser journey `BLOCKED_BROWSER_SETUP` (does not block F1).

### CVB-F1 — CV Builder UI Repair
- **Type:** FRONTEND_VISIBLE  
- **Goal:** Make existing CV Builder page load cleanly and become usable.  
- **Allowed:** CV Builder page/components/styles explicitly listed after F0; docs/tracker.  
- **Forbidden:** Advanced AI generation; new domains; frozen systems; broad redesign.  
- **Backend:** Minimal/none. **Frontend:** Route renders; sections display; L/E/E; fix imports/types.  
- **API/DB/AI:** Use existing APIs only; no new persistence unless already present.  
- **Security:** Auth page only.  
- **Tests:** Frontend build.  
- **Browser:** Load + basic edit without crash.  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F1_UI_Repair_Evidence.txt`  
- **Commit message:** `fix(cv-builder): repair CV Builder UI shell`  
- **Push:** Yes  
- **Done definition:** Usable shell with required UI states  
- **CVB-F1 outcome (2026-07-12):** Decision **B** — UI repair accepted; browser setup blocked; next = **CVB-F2**. See master § CVB-F1 CV Builder UI Repair.

### CVB-F2 — CV Builder Studio Redesign + 15-Template Gallery + Live Preview Engine
- **Type:** FRONTEND_VISIBLE  
- **Goal:** Modern CV Builder Studio with 15 structurally distinct templates + live preview.  
- **Allowed:** CV Builder FE files listed in slice prompt/addendum; docs/tracker; new gallery/preview/panel components.  
- **Forbidden:** AI rewriting; backend migrations; PDF hardening product work; save/load version product; image asset commits; global redesign.  
- **Backend:** Minimal/none (map FE templates → existing modern/classic/compact/creative for generate/export).  
- **Frontend:** Catalog registry; gallery; selected state; live preview; metadata panel; honest Preview/Save Draft/Export PDF.  
- **API/DB/AI:** No AI; existing generate/export only.  
- **Security:** Auth.  
- **Tests:** Frontend build.  
- **Browser:** Choose template → preview updates.  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F2_Template_Preview_Evidence.txt`  
- **Commit message:** `feat(frontend): add CV template gallery and preview`  
- **Push:** Yes  
- **Done definition:** Gallery + preview working for 15 approved templates  
- **CVB-F2 outcome (2026-07-12):** Decision **B** — 15-template studio accepted; browser setup blocked; next = **CVB-F3**.

### CVB-F3 — CV PDF Export Verification
- **Type:** FRONTEND_VISIBLE or FULL_STACK (export verification)  
- **Goal:** Verify and stabilize CV PDF export; wire selected template where safe.  
- **Allowed:** CV FE export flow; optional small export route/schema/document_export fixes; docs/tracker.  
- **Forbidden:** Migrations; AI rewrite; save/load product; global redesign; dist assets.  
- **Backend/Frontend:** Auth/ownership preserved; optional `template_id`; safe filename; honest UI about 4-style PDF mapping.  
- **Tests:** Frontend build + targeted document_export unit tests.  
- **Browser:** Export download journey when auth available.  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F3_PDF_Export_Evidence.txt`  
- **Commit message:** `feat(cv-builder): verify PDF export flow`  
- **Push:** Yes  
- **Done definition:** Export path verified; filename safe; template mapping documented  
- **CVB-F3 outcome (2026-07-12):** Decision **B** — accepted with browser setup blocked; next = **CVB-F4**. Capability: selected template id wired to PDF style families; full layout PDF deferred.

### CVB-F4 CV Save / Load Versions
### CVB-F4 — CV Save/Load Versions
- **Type:** FULL_STACK  
- **Goal:** Persist CV versions so users do not lose work; restore selected gallery template.  
- **Allowed:** CV version API/routes/schemas/services/models + FE save/load UI as listed; docs/tracker.  
- **Forbidden:** Cross-user access; claims ownership; Auto Apply; AI rewrite; marketplace; migration unless required.  
- **Backend:** Existing generate/list/get/delete/regenerate/export + new lightweight `PATCH /{cv_id}`; ownership via `_get_owned_cv`.  
- **Frontend:** Save Draft (create via generate or update via PATCH); Load restores content + studio template; honest status banners.  
- **DB/Migration:** None — studio template id stored in existing `section_config` JSON meta (`_studio`).  
- **AI:** None for save-settings path; generate still uses existing pipeline when creating a new version.  
- **Security/privacy:** Every CV belongs to authenticated user; ownership checks preserved.  
- **Tests:** Unit tests for studio template validation/persistence + existing export tests.  
- **Browser:** Save → refresh → load — `BLOCKED_BROWSER_SETUP` this slice.  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F4_Save_Load_Versions_Evidence.txt`  
- **Commit message:** `feat(cv-builder): persist CV versions and templates`  
- **Push:** Yes  
- **Done definition:** Persist across refresh (code-ready); ownership enforced; template restored when present  

#### Save / Load Flow Summary

| Area | Before | Change / Verification | Result | Notes |
|---|---|---|---|---|
| Saved CV list | Library list via `GET /cv-builder/` | Kept; version cards show template + selected state | Pass | Scoped CSS |
| Load CV version | Load set backend style only | `cvApi.get` + restore `studio_template_id` / default | Pass | Honest default copy |
| Save Draft | Always `generate` (new AI run) | No id → generate; has id → `PATCH` metadata | Pass | No AI on update path |
| Selected template persistence | UI-only | Persist in `section_config` `_studio` meta | Pass | 15-id validation |
| Default template fallback | N/A | Missing id → `minimal-corporate` | Pass | No scary error |
| Backend create/update/read/list | generate/list/get | + PATCH; create/read return `studio_template_id` | Pass | No migration |
| Ownership/auth check | `_get_owned_cv` | Preserved on get/patch/delete/export | Pass | Unchanged pattern |
| Export compatibility | query `template_id` | Fallback to persisted studio id then row style | Pass | 4 PDF families |
| UI loading/saving/error states | Toasts only | Banners: Saving/Draft saved/errors/load notes | Pass | `.cv-builder-save-load` |
| Build | — | `npm run build` (tsc + vite) | Pass | dist ignored |
| Backend tests | export unit tests | + `test_cv_studio_template_persistence.py` | Pass | 14 passed |
| Browser journey | — | Not run | Blocked | `BLOCKED_BROWSER_SETUP` |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `backend/app/agents/cv_builder/studio_template.py` | Added | Validate/inject/extract studio id in section_config | CVB-F4 |
| `backend/app/schemas/cv_builder.py` | Modified | `studio_template_id`, `CVUpdateRequest`, CVRead hydrate | CVB-F4 |
| `backend/app/api/routes/cv_builder.py` | Modified | PATCH update; persist on generate; export fallback | CVB-F4 |
| `backend/tests/unit/test_cv_studio_template_persistence.py` | Added | Valid/invalid/default/hydration tests | CVB-F4 |
| `frontend/src/pages/CVBuilderPage.tsx` | Modified | Save/load states + restore template | CVB-F4 |
| `frontend/src/lib/api.ts` | Modified | `studio_template_id` + `cvApi.update` | CVB-F4 |
| `frontend/src/types/api.ts` | Modified | `studio_template_id` on `GeneratedCVRead` | CVB-F4 |
| `frontend/src/styles/feature-pages.css` | Modified | Save/load + selected version styles | CVB-F4 |
| `docs/product/careerkundi_master_build_plan.md` | Modified | CVB-F4 outcome | Docs |
| `docs/product/careerkundi_live_tracker.md` | Modified | Progress → CVB-F5 | Docs |

#### Persistence Decision

`TEMPLATE_ID_PERSISTED_METADATA_FIELD`  
`SAVE_LOAD_CODE_READY_BROWSER_SETUP_BLOCKED`

#### Remaining CV Builder Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Browser-Tested Checkpoint | CVB-F5 | Full authenticated save/load/export journey |
| Full 15-layout PDF rendering | Future approved slice | Still deferred (4 CSS families) |
| AI CV rewriting | Future AI slice | Out of CVB-F4 |
| More templates beyond 15 | Future approved slice | Out of scope |

#### CVB-F4 Decision

**B CVB_F4_ACCEPTED_BROWSER_SETUP_BLOCKED**

#### Recommended Next Slice

Next slice: **CVB-F5 CV Browser-Tested Checkpoint**

- **CVB-F4 outcome (2026-07-12):** Decision **B** — code/tests/build accepted; browser save→refresh→load blocked by local setup; next = **CVB-F5**.

### CVB-F5 CV Browser-Tested Checkpoint
### CVB-F5 — CV Browser-Tested Checkpoint
- **Type:** BROWSER_CHECKPOINT  
- **Goal:** Close CV Builder stabilization with full website verification.  
- **Allowed:** Docs/tracker/evidence; tiny fixes only if journey fails and files are approved.  
- **Forbidden:** New features; scope expansion into 0051.  
- **Browser journey:** login → CV Builder → choose template → edit sections → preview → save → refresh → load → export PDF.  
- **Tests:** Build + journey + console + dist ignored.  
- **Evidence:** `~/Desktop/CareerKundi_CVB_F5_Browser_Checkpoint_Evidence.txt`  
- **Commit message:** `docs(product): record CV browser checkpoint`  
- **Push:** Yes  
- **Done definition:** Full journey PASS; acceptance gate items green  

#### Browser Journey Summary

| Journey Area | Result | Evidence | Issue Found | Follow-Up |
|---|---|---|---|---|
| runtime setup | PASS | `make dev-backend` pattern via `.venv/bin/uvicorn :8001`; `npm run dev :5173` | Docker `:8000` image pre-F4 (no PATCH) — used local `:8001` with current code | Rebuild docker backend later if needed |
| auth session | PASS | Registered `cvbf5_*@example.com` via `/api/v1/auth/register`; UI login OK | Initial CORS miss for `127.0.0.1:5173` — fixed at runtime with `CORS_ORIGINS` env (no code commit) | Prefer `localhost` or keep both origins in local `.env` |
| /cv-builder load | PASS | Studio header “Design a distinctive CV” | None | — |
| 15-template gallery | PASS | 15 `.cv-template-card` buttons | None | — |
| template preview switching | PASS | Minimal Corporate → Bold Sidebar → Editorial Modern → Engineering Blueprint | None | — |
| Save Draft | PASS | “Draft saved”; library items=1 | First save runs generate (AI/mock) — ~seconds | — |
| Load saved CV | PASS | After refresh, Load restored draft | None | — |
| selected template persistence | PASS | Engineering Blueprint restored; copy “Template restored from saved version.” | None | — |
| Export PDF | PASS | Download started | PDF style family still mapped (modern for Engineering Blueprint) | Full 15-layout PDF later |
| safe filename | PASS | `CareerKundi_CVB-F5_Engineering_Draft_Engineering_Blueprint_CV.pdf` | None | — |
| console health | PASS | No console errors | React Router v7 future-flag warnings only (pre-existing) | — |
| network health | PASS | No failed `/api` responses in journey | None | — |
| responsive quick check | PASS | 390×844 studio visible | None | — |

#### Fixes Applied

No product-code fixes were required in CVB-F5.

Runtime-only (not committed): expanded `CORS_ORIGINS` for `http://127.0.0.1:5173` when starting local uvicorn on `:8001`.

#### CV Builder Stabilization Decision

`CV_BUILDER_BROWSER_CHECKPOINT_PASSED_WITH_MINOR_LIMITATIONS`

Known remaining limitation (honest UI copy): PDF export maps studio templates to 4 CSS style families (modern/classic/compact/creative), not full 15-layout PDF parity.

#### Remaining CV Builder Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Full 15-layout PDF rendering | Future approved slice | Still deferred; 4 CSS families |
| AI CV rewriting | Future AI slice | Out of CVB |
| Additional template polish | Future approved slice | Optional |
| Mobile polish | Future if needed | Quick check OK at 390px |

#### CVB-F5 Decision

**B CVB_F5_BROWSER_CHECKPOINT_ACCEPTED_WITH_MINOR_LIMITATIONS**

#### Recommended Next Slice

Next slice: **ROAD-F0 Roadmap Audit**

- **CVB-F5 outcome (2026-07-12):** Decision **B** — authenticated browser journey PASS (save/load/template restore/export); minor limitation = 4-family PDF mapping; next = **ROAD-F0**.

### ROAD-F0 Roadmap Audit
### ROAD-F0 — Roadmap Audit
- **Type:** AUDIT_ONLY  
- **Goal:** Document current roadmap routes/components/APIs vs platform-wide placement; define F1–F4.  
- **Allowed:** Docs/tracker/evidence; read-only inspect.  
- **Forbidden:** Product code; Graduate Launch ownership confusion in docs.  
- **Product code allowed:** No  
- **Browser:** Open `/roadmap` and record behavior.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F0_Roadmap_Audit_Evidence.txt`  
- **Commit message:** `docs(product): record Roadmap audit`  
- **Push:** Optional/yes  
- **Done definition:** Audit complete; F1–F4 scoped  

#### Current Roadmap Route Inventory

| Route | Page / Component | Access | Current Status | Source File | Notes |
|---|---|---|---|---|---|
| `/roadmap` | `RoadmapPage` | Auth + AppShell | EXISTING_VERIFIED | `frontend/src/App.tsx`, `pages/RoadmapPage.tsx` | Sidebar “Career Roadmap”; browser load PASS (empty state) |
| `/roadmaps` | — | Auth expected | MISSING | — | Browser: Not Found; master-plan plural target |
| `/roadmaps/new` | — | — | PLANNED | — | Generate lives as modal on `/roadmap` today |
| `/roadmaps/:id` | — | — | PLANNED | — | Detail is in-page selection on `/roadmap` |
| `/roadmaps/:id/tasks` | — | — | PLANNED | — | Skill status tracking exists; no separate tasks route |
| `/graduate-launch` | — | — | PLANNED | — | After 0056; must not own Roadmaps |

#### Current Frontend Roadmap Inventory

| Area | Verified File / Component | Current Behavior | Status | Notes |
|---|---|---|---|---|
| page component | `pages/RoadmapPage.tsx` | Hero + generate modal + timeline/kanban + skill modal | EXISTING_VERIFIED | Large page-local UI |
| route registration | `App.tsx` lazy `/roadmap` | Singular path only | EXISTING_VERIFIED | No `/roadmaps*` |
| sidebar nav | `Sidebar.tsx` | “Career Roadmap” → `/roadmap` | EXISTING_VERIFIED | Career Tools group |
| roadmap list | `RoadmapPage` chip row when >1 | Selects active roadmap | EXISTING_VERIFIED | Not a dedicated library page |
| create/generate flow | `GenerateModal` + `roadmapApi.generate` | Target role, pace, level, hours, context | EXISTING_VERIFIED | Sample role chips (tech-heavy list) |
| detail view | Same page | Progress bar, radar, milestones/skills | EXISTING_VERIFIED | |
| milestone display | `TimelineView` | Expandable milestone cards + skill chips | EXISTING_VERIFIED | CSS `.roadmap-timeline*` |
| task display | Skill chips / kanban columns | Skills as work units (not separate Task model) | PARTIAL_EXISTING | Naming: skills ≠ tasks |
| progress tracking | Skill status cycle + % bar | PATCH skill status | EXISTING_VERIFIED | |
| API calls | `lib/api.ts` `roadmapApi` | list/get/generate/regenerate/updateSkillStatus/refreshSkill/delete | EXISTING_VERIFIED | delete/regenerate unused in UI |
| types | `types/api.ts` `RoadmapRead*` | Matches milestones/skills | EXISTING_VERIFIED | No roadmap-level `status` field |
| loading state | Spinner while list loads | Present | EXISTING_VERIFIED | |
| empty state | “No roadmap yet” + Generate CTA | Present | EXISTING_VERIFIED | Browser PASS |
| error state | Toasts on mutate; no list `isError` UI | PARTIAL_EXISTING | List failure not surfaced as banner |
| success state | Toast on generate / refresh | Present | EXISTING_VERIFIED | |
| mobile/responsive | `feature-page` + kanban 3-col grid | Hero wraps; kanban may crowd | EXISTING_NEEDS_REVIEW | ROAD-F1 polish if needed |
| dashboard widget | `DashboardPage.tsx` | Shows active roadmap % | EXISTING_NEEDS_REVIEW | Uses `r.status==="active"` and `milestone.status` — fields not on models (falls back / misleading) |
| SkillRadar | `components/features/SkillRadar.tsx` | Radar chart | EXISTING_VERIFIED | |
| platform-wide copy | Roadmap hero subtitle | Generic career path; not Graduate-only | EXISTING_VERIFIED | Browser: no Graduate Launch framing |

#### Current Backend Roadmap Inventory

| Backend Area | Verified File / Endpoint | Current Behavior | Status | Notes |
|---|---|---|---|---|
| routes | `api/routes/roadmap.py` | generate, list, get, delete, regenerate, skill status, skill refresh | EXISTING_VERIFIED | Prefix `/api/v1/roadmap` |
| schemas | `schemas/roadmap.py` | Generate request + Read models + skill status update | EXISTING_VERIFIED | |
| agents | `agents/roadmap/{graph,agents,mock_data,state}.py` | Multi-node generation + skill refresh | EXISTING_VERIFIED | Mock/live via LLM keys |
| models/storage | `db/models/roadmap.py` | `Roadmap`, `RoadmapMilestone`, `RoadmapSkill` | EXISTING_VERIFIED | Tables in foundation baseline |
| generation logic | `run_roadmap_generation_pipeline` | Persists milestones/skills JSON blobs | EXISTING_VERIFIED | Role-targeted pathway |
| save/load | ORM persist on generate; list/get | EXISTING_VERIFIED | No separate “versions” API |
| task/milestone | Milestone + skill rows; skill status | PARTIAL_EXISTING | No Task entity; skill status is progress |
| auth/ownership | `_get_owned_roadmap` / `_get_owned_skill` | EXISTING_VERIFIED | user_id scoped |
| tests | `backend/tests` | No dedicated roadmap test files found | MISSING | `pytest -k roadmap…` → 0 selected |
| OpenAPI | Live `:8001` | Paths match route file | EXISTING_VERIFIED | |

#### Current Roadmap Capability Matrix

| Capability | Current Status | Evidence | Gap | Target Slice |
|---|---|---|---|---|
| route exists | Yes | `/roadmap` in App + Sidebar | Plural `/roadmaps*` missing | ROAD-F1 (clarify); later alias |
| page loads | Yes | Browser PASS | — | ROAD-F1 if regressions |
| roadmap list visible | Partial | Chip selector when >1 | No dedicated list page | ROAD-F1 |
| empty state exists | Yes | Browser empty CTA | — | ROAD-F1 keep |
| create/generate roadmap exists | Yes | Generate modal + API | Sample roles tech-heavy | ROAD-F1 copy; Future engine for plan types |
| roadmap detail exists | Yes | In-page detail | No `/roadmaps/:id` | ROAD-F3 route polish later |
| milestones visible | Yes | TimelineView | — | ROAD-F3 polish |
| tasks visible | Partial | Skills as tasks | No Task model/UI label | ROAD-F3 |
| task completion tracking | Yes | Skill status PATCH | Dashboard milestone.status bug | ROAD-F1/F3 |
| progress indicator | Yes | % bar + radar | — | ROAD-F1 keep |
| save/load persistence | Yes | DB + list/get | No explicit version UX; delete UI missing | ROAD-F2 |
| auth/ownership protection | Yes | `_get_owned_*` | Keep | ROAD-F2 tests |
| loading/empty/error states | Partial | Load+empty OK; list error weak | Add list error UI | ROAD-F1 |
| mobile usability | Partial | Page loads; kanban 3-col | Verify narrow layout | ROAD-F1 / F4 |
| browser journey verified | Partial | Audit observation only | Full generate→track in F4 | ROAD-F4 |

#### Gap Analysis Against Master Plan

**Exists:** Authenticated `/roadmap` page with generate, list/select, milestone timeline, kanban-by-skill-status, skill study/practice modal, markdown export, and full ownership-checked CRUD-ish API + agent pipeline + DB models.

**Partial:** Progress “tasks” are skills; delete/regenerate APIs unused in UI; dashboard progress math inconsistent with schema; list error UX thin; sample roles skew tech.

**Broken / risky:** Dashboard assumes `roadmap.status` and `milestone.status` (neither on `Roadmap` / `RoadmapMilestone` models) — active selection falls back to `[0]`; milestone complete count likely always 0. Plural routes `/roadmaps*` 404.

**Missing:** Master-plan plural IA; specialized plan types (skill gap / career switch / graduate launch / study abroad / public sector); dedicated backend tests; Graduate Launch route (correctly later).

**Route naming:** Current singular `/roadmap` is live; master plan target `/roadmaps` is planned — do not invent plural as existing. ROAD-F1 should keep singular working and state platform-wide copy; alias later.

**Graduate Launch:** Current Roadmap UI is not Graduate-only. Keep it that way.

**Must not build yet in F1:** Full engine rewrite, new plan taxonomies, DB migrations for new entities, AI architecture overhaul, sidebar redesign.

**ROAD-F1 focus:** Usable shell — load, empty/list clarity, create CTA, honest platform-wide copy, loading/empty/error honesty, optional dashboard status bugfix if in allowed F1 files.

#### Roadmap Risk Register

| Risk | Impact | Evidence | Recommended Handling | Target Slice |
|---|---|---|---|---|
| Singular vs plural route mismatch | Nav/docs confusion | `/roadmap` works; `/roadmaps` 404 | Keep singular in F1; plan alias | ROAD-F1 / later |
| Graduate Launch confusion | Wrong ownership | Copy OK today; planned `/graduate-launch` separate | Keep platform-wide framing | ROAD-F1 |
| Generic / tech-skewed generation | Narrow personas | SAMPLE_ROLES tech list; any free-text role allowed | Broaden copy/CTA; engine later | ROAD-F1 / Future |
| Missing delete/regenerate UI | Orphan roadmaps | API exists; no page buttons | Add minimal controls | ROAD-F2 |
| Dashboard status field mismatch | Wrong progress | `r.status`, `m.status` absent on models | Fix dashboard mapping | ROAD-F1 if allowed else F3 |
| No roadmap backend tests | Regressions | 0 pytest matches | Add ownership/API tests | ROAD-F2 |
| List error silent | Stuck spinner/blank | No `isError` on list query | Error banner + retry | ROAD-F1 |
| Kanban mobile crowding | Usability | Fixed 3-column grid | Responsive stack | ROAD-F1 / F4 |
| Browser full journey not done | Unknown generate latency/UX | Audit observed empty load only | Full journey | ROAD-F4 |
| AI-heavy without structure | Cost/quality | 9-node agent exists with mock | Do not expand in F1 | Future engine |

#### ROAD-F1 Repair Scope Recommendation

**In scope for ROAD-F1:**
- Ensure `/roadmap` loads cleanly with clear platform-wide copy (not Graduate-only).
- Preserve/improve empty state + “Generate / New roadmap” CTA.
- Clarify list/select of existing roadmaps when present.
- Loading / empty / list-error honesty.
- Optional: fix Dashboard roadmap progress field misuse if Dashboard is approved in F1 allowed files — otherwise document for later.
- No new AI architecture; no new migrations unless page is unusable without them (unlikely).

**Out of scope for ROAD-F1:**
- Full Roadmap Engine / specialized plan types
- Plural `/roadmaps*` IA implementation (unless trivial alias approved later)
- Full task-tracking redesign
- Public sector / study abroad / career-switch intelligence
- Large redesign outside Roadmap page / approved files

#### ROAD-F0 Decision

**A ROADMAP_READY_FOR_ROAD_F1_UI_REPAIR**

Recommended next slice: **ROAD-F1 Roadmap UI Repair**

#### ROAD-F0 Audit-Only Decision

ROAD-F0 is audit-only.  
No Roadmap frontend product code was modified.  
No Roadmap backend product code was modified.  
Any repair must happen in ROAD-F1 or later.

- **ROAD-F0 outcome (2026-07-12):** Decision **A** — route/page/API exist; browser empty-state PASS; `/roadmaps` missing; next = **ROAD-F1**.

### ROAD-F1 — Roadmap UI Repair
- **Type:** FRONTEND_VISIBLE  
- **Goal:** Make Roadmap page load and display a usable surface.  
- **Allowed:** Roadmap page/components listed after F0; docs/tracker.  
- **Forbidden:** Full AI roadmap engine; Graduate-only ownership of all roadmaps; 004E/Auto Apply.  
- **Frontend:** Route exists; list or empty; create CTA.  
- **Backend/API/DB/AI:** Minimal/none; no full AI engine.  
- **Tests:** Frontend build.  
- **Browser:** List/empty/CTA.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F1_UI_Repair_Evidence.txt`  
- **Commit message:** `fix(roadmaps): repair Roadmap UI shell`  
- **Push:** Yes  
- **Done definition:** Usable list/empty/CTA surface  

### ROAD-F2 — Roadmap Save/Load Contract
- **Type:** FULL_STACK if persistence missing  
- **Goal:** Persist roadmaps with ownership.  
- **Allowed:** Roadmap API/FE files listed after F0/F1; docs/tracker.  
- **Forbidden:** Cross-user access; inventing endpoints as existing without verify.  
- **API shape (planned):** `GET/POST /api/v1/roadmaps`, `GET/PATCH /api/v1/roadmaps/{id}`, task routes as needed — verify before coding.  
- **Security:** Belongs to user/subject; ownership checks.  
- **Tests:** API ownership + create/refresh.  
- **Browser:** Create → refresh → still present.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F2_Save_Load_Contract_Evidence.txt`  
- **Commit message:** `feat(roadmaps): add roadmap save and load contract`  
- **Push:** Yes  
- **Done definition:** Persist + ownership enforced  

### ROAD-F3 — Roadmap Detail + Task Tracking
- **Type:** FULL_STACK  
- **Goal:** Detail with milestones, tasks, completion, progress, persistence.  
- **Allowed:** Detail/task FE + matching API files listed in prompt; docs/tracker.  
- **Forbidden:** Taxonomy intelligence requiring 0051; Graduate Launch takeover.  
- **Frontend:** Timeline; milestone cards; task list; completion; progress.  
- **Backend/API:** Task create/update as needed with ownership.  
- **Tests:** API + UI.  
- **Browser:** Complete task → refresh persist.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F3_Detail_Task_Tracking_Evidence.txt`  
- **Commit message:** `feat(roadmaps): add roadmap detail and task tracking`  
- **Push:** Yes  
- **Done definition:** Detail + tasks persist  

### ROAD-F4 — Roadmap Browser-Tested Checkpoint
- **Type:** BROWSER_CHECKPOINT  
- **Goal:** Close Roadmap stabilization with full website verification.  
- **Allowed:** Docs/tracker/evidence; tiny approved fixes only if journey fails.  
- **Forbidden:** Jumping to 0051 without gate; new engines.  
- **Browser journey:** login → Roadmaps → create/open → complete task → refresh → progress persists.  
- **Tests:** Build + journey + console + dist ignored.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F4_Browser_Checkpoint_Evidence.txt`  
- **Commit message:** `test(roadmaps): record Roadmap browser checkpoint`  
- **Push:** Yes  
- **Done definition:** Full journey PASS; ready for pre-0051 UX checkpoint  

---

## 44. Key Technical Slice Notes

See Section 43 cards for UX0-S2…ROAD-F4 and UX0-S5 checkpoint. Additional emphasis:

- **UX0-S5:** UX0 planning closed; next = PF11-R1.  
- **PF11-R1:** subjects/goals only; no claims UI creep; audit-first.  
- **CVB-F0 / ROAD-F0:** implementation not allowed.  
- **CVB-F4 / ROAD-F2:** ownership checks mandatory on every object route.  
- **Do not jump to 0051** until PF11/CVB/ROAD checkpoints complete or deferred by ADR.

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
