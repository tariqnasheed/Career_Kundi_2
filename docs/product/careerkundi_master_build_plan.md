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

### Gemini function calling (legacy research note)

**Status:** Historical / deprecated for CareerKundi’s active provider path.  
**Current LLM provider:** Local Ollama 8B — see **LLM-R1**.  
**Source (historical):** Google Gemini API documentation — Function Calling  
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
| ROAD-F1 | Roadmap UI Repair | Usable list | After F0 | Minimal | Roadmap page | None | No full AI engine | — | Build | List/empty/CTA | ROAD-F1 | Yes | No | ROAD files | Yes | Done (Decision A) |
| ROAD-F2 | Save/Load Contract | Persist roadmaps | After F1 | Roadmap APIs | Save/load | Maybe | None | Ownership | API tests | Create/refresh | ROAD-F2 | Yes | If contract | ROAD+API | Yes | Done (Decision A) |
| ROAD-F3 | Detail + Tasks | Tracking | After F2 | Tasks API | Detail UI | Maybe | None | Ownership | API+UI | Complete task persist | ROAD-F3 | Yes | No | ROAD files | Yes | Done (Decision A) |
| ROAD-F4 | Browser Checkpoint | Close ROAD | After F3 | — | — | — | — | — | Full | Full roadmap journey | ROAD-F4 | Yes | No | evidence | Yes | Done (Decision B) |
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

### ROAD-F1 Roadmap UI Repair
### ROAD-F1 — Roadmap UI Repair
- **Type:** FRONTEND_VISIBLE  
- **Goal:** Make Roadmap page load and display a usable surface.  
- **Allowed:** Roadmap page/components listed after F0; docs/tracker; minimal App alias; Dashboard widget mismatch fix.  
- **Forbidden:** Full AI roadmap engine; Graduate-only ownership of all roadmaps; 004E/Auto Apply; migrations.  
- **Frontend:** Route exists; list or empty; create CTA; loading/error honesty; platform-wide copy.  
- **Backend/API/DB/AI:** None changed.  
- **Tests:** Frontend build.  
- **Browser:** List/empty/CTA + `/roadmaps` alias.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F1_Roadmap_UI_Repair_Evidence.txt`  
- **Commit message:** `feat(frontend): repair Roadmap UI`  
- **Push:** Yes  
- **Done definition:** Usable list/empty/CTA surface  

#### Repair Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| Roadmap page load | Loaded | Kept + clearer shell | Pass | Browser PASS |
| Platform-wide copy | Generic learning path | Platform-wide hero + pathway examples + footnote | Pass | Not Graduate-only |
| Loading state | Spinner only | Status strip + spinner | Pass | |
| Empty state | Basic CTA | Examples + honest empty + Generate CTA | Pass | |
| Error state | Missing for list | List/detail error + Retry | Pass | Code path |
| Roadmap list | Chips when >1 | Card list always when saved | Pass | |
| CTA | New roadmap | New / Generate CTAs | Pass | |
| Milestone/skill display | Skill % OK | Honest skill-status copy | Pass | No fake task tracker |
| Dashboard roadmap widget | Fake milestone.status | Skill-based % + Continue CTA | Pass | Fixed |
| `/roadmap` route | Existing | Unchanged live route | Pass | |
| `/roadmaps` route behavior | 404 | Minimal alias → RoadmapPage | Pass | Alias added |
| Responsive behavior | Kanban 3-col | Stack at ≤720px | Pass | Quick check |
| Browser journey | Audit empty only | Auth + /roadmap + /roadmaps + dashboard | Pass | |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/RoadmapPage.tsx` | Modified | UI repair shell | ROAD-F1 |
| `frontend/src/pages/DashboardPage.tsx` | Modified | Status mismatch fix | ROAD-F1 |
| `frontend/src/App.tsx` | Modified | `/roadmaps` alias | ROAD-F1 |
| `frontend/src/styles/feature-pages.css` | Modified | Status/list/help/responsive | ROAD-F1 |
| `docs/product/careerkundi_master_build_plan.md` | Modified | Outcome | Docs |
| `docs/product/careerkundi_live_tracker.md` | Modified | Progress → F2 | Docs |

#### Route Decision

`ROUTE_ALIAS_ROADMAPS_ADDED`

- `/roadmap` remains the primary live route (sidebar unchanged).
- `/roadmaps` aliases to the same `RoadmapPage` (minimal App.tsx addition).
- Full plural IA (`/roadmaps/new`, `/:id`, `/:id/tasks`) remains planned for later.

#### Dashboard Widget Decision

`DASHBOARD_WIDGET_STATUS_MISMATCH_FIXED`

- Removed `roadmap.status === "active"` and `milestone.status === "completed"`.
- Progress now uses `skill.status === "completed"` over flattened skills; latest list item as active.

#### Remaining Roadmap Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Roadmap Save/Load Contract | ROAD-F2 | Delete UI, regenerate UX, ownership tests |
| Roadmap Detail + Task Tracking | ROAD-F3 | Task model/UI beyond skills |
| Roadmap Browser-Tested Checkpoint | ROAD-F4 | Full generate→track journey |
| Full Roadmap Engine / advanced generation | Future engine slice | Specialized plan types |
| Specialized roadmap pathways | Future pathway slices | Public sector, study abroad, etc. |

#### ROAD-F1 Decision

**A ROAD_F1_UI_REPAIR_ACCEPTED_READY_FOR_ROAD_F2**

#### Recommended Next Slice

Next slice: **ROAD-F2 Roadmap Save/Load Contract**

- **ROAD-F1 outcome (2026-07-12):** Decision **A** — UI shell repaired; `/roadmaps` alias; Dashboard skill progress fixed; next = **ROAD-F2**.

### ROAD-F2 Roadmap Save / Load Contract
### ROAD-F2 — Roadmap Save/Load Contract
- **Type:** FULL_STACK_CONTRACT_STABILIZATION  
- **Goal:** Persist roadmaps with ownership; stabilize create/list/get/delete/regenerate UI contract.  
- **Allowed:** Roadmap API/FE files listed after F0/F1; docs/tracker; targeted tests.  
- **Forbidden:** Cross-user access; inventing endpoints; Task model; migrations; full engine.  
- **API shape (verified):** Existing singular `/api/v1/roadmap*` (generate/list/get/delete/regenerate/skill status/refresh).  
- **Security:** `_get_owned_roadmap` / user-scoped list preserved.  
- **Tests:** `backend/tests/unit/test_roadmap_contract.py` (7 passed).  
- **Browser:** Create → list → load → refresh persist → `/roadmaps` alias.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F2_Save_Load_Contract_Evidence.txt`  
- **Commit message:** `feat(roadmap): stabilize save load contract`  
- **Push:** Yes  
- **Done definition:** Persist + ownership enforced + UI contract stable  

#### Contract Summary

| Area | Before | Change / Verification | Result | Notes |
|---|---|---|---|---|
| Roadmap list | Loaded via `GET /roadmap/` | Kept; clearer success strip | Pass | Browser PASS |
| Create/generate roadmap | Generated but did not auto-select | Select + success toast/strip after create | Pass | Live LLM ok |
| Load/select roadmap | Auto-select first / card click | Explicit load success message | Pass | |
| Detail rendering | Skills/milestones | Unchanged fields; honest progress copy | Pass | |
| Milestone/skill progress | Skill status only | Confirmed; no roadmap/milestone status | Pass | |
| Delete/regenerate if present | API existed; UI missing | Wired Delete + Regenerate w/ confirm | Pass | |
| Frontend API methods | list/get/generate/regen/delete/skills | Return types aligned; regenerate payload expanded | Pass | |
| Frontend types | Required `user_id`; strict urls | Optional `user_id`; nullable url; personalization_inputs | Pass | Matches BE schema |
| Backend routes | Existing ownership routes | No route rewrite | Pass | Verified |
| Backend schemas | Truthful Read models | Unchanged; tests lock contract | Pass | |
| Auth/ownership | `_get_owned_*` | Preserved; tested via source contract | Pass | |
| Platform-wide copy | F1 watch item | Re-verified in browser | Pass | See Platform Copy Decision |
| `/roadmap` route | Live | Stable | Pass | |
| `/roadmaps` alias | F1 alias | Stable | Pass | |
| Browser journey | F1 shell only | Full create→refresh→alias | Pass | |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/RoadmapPage.tsx` | Modified | Create select + delete/regen + success states | ROAD-F2 |
| `frontend/src/lib/api.ts` | Modified | Skill return types; regenerate payload | ROAD-F2 |
| `frontend/src/types/api.ts` | Modified | Align Roadmap types with backend | ROAD-F2 |
| `frontend/src/styles/feature-pages.css` | Modified | Success/detail/progress scoped classes | ROAD-F2 |
| `backend/tests/unit/test_roadmap_contract.py` | Added | Schema + ownership contract tests | ROAD-F2 |
| `docs/product/careerkundi_master_build_plan.md` | Modified | Outcome | Docs |
| `docs/product/careerkundi_live_tracker.md` | Modified | Progress → F3 | Docs |

#### Save / Load Contract Decision

`ROADMAP_SAVE_LOAD_CONTRACT_STABILIZED`

#### Platform Copy Decision

`PLATFORM_COPY_VERIFIED_PASS`  
(ROAD-F1 `platform_copy` script mismatch explained as `PLATFORM_COPY_SCRIPT_ASSERTION_WAS_TOO_NARROW` — eyebrow/subtitle/empty copy are platform-wide; browser recheck PASS.)

#### Test Decision

`ROADMAP_CONTRACT_TESTS_ADDED_AND_PASSING` (7 passed)

#### Remaining Roadmap Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Roadmap Detail + Task Tracking | ROAD-F3 | Task model/UI beyond skills |
| Roadmap Browser-Tested Checkpoint | ROAD-F4 | Full generate→track journey gate |
| Full Roadmap Engine / advanced generation | Future engine slice | Specialized plan types |
| Specialized roadmap pathways | Future pathway slices | Public sector, study abroad, etc. |

#### ROAD-F2 Decision

**A ROAD_F2_SAVE_LOAD_ACCEPTED_READY_FOR_ROAD_F3**

#### Recommended Next Slice

Next slice: **ROAD-F3 Roadmap Detail + Task Tracking**

- **ROAD-F2 outcome (2026-07-12):** Decision **A** — save/load contract stabilized; delete/regen UI wired; contract tests added; next = **ROAD-F3**.

### ROAD-F3 Roadmap Detail + Task Tracking
### ROAD-F3 — Roadmap Detail + Task Tracking
- **Type:** ROADMAP_DETAIL_AND_TRACKING  
- **Goal:** Clear selected-roadmap detail; skill-based progress/action tracking; persist status updates.  
- **Allowed:** Roadmap FE detail/tracker; existing skill status/refresh APIs; docs/tracker; targeted tests.  
- **Forbidden:** New Task model/migration; full Roadmap Engine; pathway packs; sidebar redesign.  
- **Frontend:** Progress summary by skill status; Skill progress tracker; explicit status selects; refresh/regen/delete remain.  
- **Backend/API:** Existing skill status/refresh ownership endpoints unchanged (tests extended).  
- **Tests:** Extended `test_roadmap_contract.py` (9 passed; 11 with skill filter).  
- **Browser:** Generate → tracker → status update → refresh persist → alias.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F3_Detail_Task_Tracking_Evidence.txt`  
- **Commit message:** `feat(roadmap): add detail tracking controls`  
- **Push:** Yes  
- **Done definition:** Detail + skill status tracking persist  

#### Detail + Tracking Summary

| Area | Before | Change / Verification | Result | Notes |
|---|---|---|---|---|
| Selected roadmap detail | Summary + timeline/kanban | Progress counts + honesty copy + tracker | Pass | |
| Milestone display | Timeline milestones | Kept; skill % per milestone | Pass | |
| Skill tracker | Chip cycle-only | Dedicated tracker + status select | Pass | |
| Skill status update | Cycle icon; weak feedback | Select + success/error strip | Pass | Persisted |
| Skill refresh | Modal only | Tracker Refresh + modal | Pass | Present |
| Progress summary | Completed/total only | Counts by not_started/in_progress/completed | Pass | Skill-derived |
| Regenerate roadmap | F2 wired | Still present | Pass | |
| Delete roadmap | F2 wired | Still present | Pass | Visual |
| Copy honesty | Skill unit note | Explicit “skills are progress units” | Pass | DETAIL_COPY_VERIFIED_PASS |
| `/roadmap` route | Live | Stable | Pass | |
| `/roadmaps` alias | F1/F2 | Stable | Pass | |
| Browser journey | F2 create/load | Status update + persist | Pass | |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/RoadmapPage.tsx` | Modified | Tracker, status selects, progress counts | ROAD-F3 |
| `frontend/src/styles/feature-pages.css` | Modified | Tracker/detail scoped styles | ROAD-F3 |
| `backend/tests/unit/test_roadmap_contract.py` | Modified | Skill ownership + no-Task contract | ROAD-F3 |
| `docs/product/careerkundi_master_build_plan.md` | Modified | Outcome | Docs |
| `docs/product/careerkundi_live_tracker.md` | Modified | Progress → F4 | Docs |

#### Tracking Decision

`SKILL_BASED_TRACKING_STABILIZED`

#### Task Model Decision

`NO_TASK_MODEL_SKILLS_ARE_PROGRESS_UNITS`

#### Test Decision

`ROADMAP_CONTRACT_TESTS_EXTENDED_AND_PASSING` (9 in file; 11 with `-k skill`)

#### Remaining Roadmap Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Roadmap Browser-Tested Checkpoint | ROAD-F4 | Full journey gate |
| Full Roadmap Engine / advanced generation | Future engine slice | Specialized plan types |
| Specialized roadmap pathways | Future pathway slices | Public sector, study abroad, etc. |
| Separate task model, if approved | Future task-tracking architecture slice | Not in ROAD-F3 |

#### ROAD-F3 Decision

**A ROAD_F3_DETAIL_TRACKING_ACCEPTED_READY_FOR_ROAD_F4**

#### Recommended Next Slice

Next slice: **ROAD-F4 Roadmap Browser-Tested Checkpoint**

- **ROAD-F3 outcome (2026-07-12):** Decision **A** — skill-based detail tracking stabilized; next = **ROAD-F4**.

### ROAD-F4 Roadmap Browser-Tested Checkpoint
### ROAD-F4 — Roadmap Browser-Tested Checkpoint
- **Type:** BROWSER_CHECKPOINT  
- **Goal:** Close Roadmap stabilization with full website verification.  
- **Allowed:** Docs/tracker/evidence; tiny approved Roadmap fixes if journey fails.  
- **Forbidden:** Jumping to 0051 without gate; new engines; Task model; shell rewrite.  
- **Browser journey:** login → `/roadmap` + `/roadmaps` → generate → detail/tracker → skill status persist → refresh skill → delete disposable → console/network.  
- **Tests:** Build + contract tests + journey.  
- **Evidence:** `~/Desktop/CareerKundi_ROAD_F4_Browser_Checkpoint_Evidence.txt`  
- **Commit message:** `fix(roadmap): pass browser checkpoint` (product fixes applied)  
- **Push:** Yes  
- **Done definition:** Full journey PASS; ready for post-CV/Roadmap UX checkpoint  

#### Browser Journey Summary

| Journey Area | Result | Evidence | Issue Found | Follow-Up |
|---|---|---|---|---|
| runtime setup | Pass | fe:200 api:401 | — | — |
| auth session | Pass | UI register | — | — |
| `/roadmap` route | Pass | Playwright | — | — |
| `/roadmaps` alias | Pass | Playwright | — | — |
| platform-wide copy | Pass | eyebrow + honesty copy | — | — |
| roadmap list | Pass | list after generate | — | — |
| generate roadmap | Pass | 201 + skills after fix | Live LLM taxonomy failure → empty skills | Fallback fix |
| load/select roadmap | Pass | card + detail | — | — |
| selected roadmap detail | Pass | detail grid | — | — |
| milestone display | Pass | timeline | — | — |
| skill tracker | Pass | selects present | Empty when LLM failed | Fallback + empty copy |
| skill status update | Pass | not_started→completed | — | — |
| status persistence after refresh | Pass | reload select value | — | — |
| progress summary | Pass | status counts | — | — |
| refresh skill | Pass | toast success | — | — |
| regenerate roadmap | Pass | control present | Executed visually only on primary | Future optional |
| delete roadmap | Pass | disposable deleted; no 404 | Post-delete detail refetch 404 | Cancel/remove query fix |
| console health | Pass | no errors after fix | — | — |
| network health | Pass | no failed roadmap APIs after fix | — | — |
| responsive check | Pass w/ limitation | 390/768/1280 | Shell overflow at 390 | Shell slice |

#### Fixes Applied

| File | Bug | Fix | Why Allowed |
|---|---|---|---|
| `backend/app/agents/roadmap/agents.py` | Live RoleTaxonomy LLM failure persisted empty skill roadmaps | Catch LLM errors; fall back to `mock_data.infer_required_skills` | Direct runtime contract fix |
| `frontend/src/pages/RoadmapPage.tsx` | Delete left detail query refetching deleted id (404); empty tracker silent | Cancel/remove detail query + optimistic list filter; empty tracker message | Direct Roadmap checkpoint bugs |
| `frontend/src/styles/feature-pages.css` | Empty tracker styling | `.roadmap-skill-tracker__empty` | Scoped Roadmap CSS |

#### Roadmap Stabilization Decision

`ROADMAP_BROWSER_CHECKPOINT_PASSED_WITH_MINOR_LIMITATIONS`

#### Known Limitations

- Known app-shell horizontal overflow at 390px; shell-level fix deferred.
- No separate Task model; skills remain current progress units.
- Full advanced Roadmap Engine remains future work.
- Specialized pathway packs remain future work.
- Live LLM taxonomy may fail; keyword fallback keeps generate usable (not full AI engine rewrite).

#### Remaining Roadmap Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| Full Roadmap Engine / advanced generation | Future engine slice | Beyond fallback |
| Specialized roadmap pathways | Future pathway slices | Public sector, study abroad, etc. |
| Separate task model if approved | Future task architecture slice | Not in ROAD-* |
| Shell/mobile overflow | Future app-shell responsive slice | Confirmed at 390 |

#### ROAD-F4 Decision

**B ROAD_F4_BROWSER_CHECKPOINT_ACCEPTED_WITH_MINOR_LIMITATIONS**

#### Recommended Next Slice

Next slice: **UX-CHECKPOINT-1 Post-CV-and-Roadmap UX Checkpoint**

- **ROAD-F4 outcome (2026-07-12):** Decision **B** — Roadmap ladder closed with minor shell overflow limitation; next = **UX-CHECKPOINT-1**.

### UX-CHECKPOINT-1 Post-CV-and-Roadmap UX Checkpoint
- **Type:** CROSS_FEATURE_UX_CHECKPOINT  
- **Goal:** Verify auth/shell, CV Builder, Roadmap, and primary routes before 0051.  
- **Allowed:** Docs/tracker; tiny UX blockers only if journey fails.  
- **Forbidden:** 0051 implementation; shell redesign; new engines; migrations.  
- **Evidence:** `~/Desktop/CareerKundi_UX_Checkpoint_1_Evidence.txt`  
- **Commit message:** `docs(product): record post-CV Roadmap UX checkpoint`  
- **Push:** Yes  

#### Cross-Feature Browser Journey Summary

| Journey Area | Result | Evidence | Issue Found | Follow-Up |
|---|---|---|---|---|
| auth/session | Pass | UI register → `/dashboard` | — | — |
| dashboard | Pass | load + widgets | — | — |
| navigation shell | Pass | sidebar/header on routes | — | — |
| CV Builder route | Pass | Studio loads | — | — |
| CV 15-template gallery | Pass | gallery candidates present; non-default select | — | — |
| CV save/load | Pass | Save Draft → Draft saved; library/persist | Generate can take ~20s | Watch latency |
| CV export | Pass | PDF `CareerKundi_Candidate_Minimal_Corporate_CV.pdf` | Export disabled until draft exists | Honest |
| Roadmap route | Pass | `/roadmap` | — | — |
| Roadmaps alias | Pass | `/roadmaps` | — | — |
| Roadmap generate/load | Pass | Data Analyst + skills | — | — |
| Roadmap skill tracking | Pass | status persist after reload | — | — |
| Dashboard widgets | Pass | no fake roadmap.status; no CV overclaim | — | — |
| Profile route | Pass | loads | — | — |
| Settings route | Pass | loads | — | — |
| Jobs route | Pass | loads | — | — |
| Platform route | Pass load | page loads | CORS on `/platform/subjects` console errors | Watch / PF11 follow-up |
| console health | Acceptable | no CV/Roadmap journey breakers | Platform CORS noise | Watch |
| network health | Acceptable | CV/Roadmap APIs OK | Platform subjects CORS | Watch |
| 390px responsive check | Usable | overflow observed | Shell overflow | Shell slice |
| 768px responsive check | Pass | usable; CV overflow minor | CV studio width | Watch |
| desktop check | Pass | no overflow | — | — |

#### Fixes Applied

No product-code fixes were required in UX-CHECKPOINT-1.

#### Known Limitations

- CV PDF uses 4 CSS style families, not full 15-layout rendering.
- Roadmap has no separate Task model; skills are current progress units.
- App-shell horizontal overflow at 390px observed but usable.
- Advanced Roadmap Engine remains future work.
- Specialized pathway packs remain future work.
- Old 004E repair remains frozen/deferred.
- Old Auto Apply repair remains frozen/deferred.
- Platform subjects CORS console noise observed; page still loads (watch item).

#### Readiness Decision

`READY_FOR_0051_WITH_WATCH_ITEMS`

#### Recommended Next Slice

Next slice: **0051 Universal Role & Pathway Taxonomy Planning**

#### 0051 Entry Guardrails

- 0051 must not break CV Builder.
- 0051 must not break Roadmap.
- 0051 must preserve browser-tested flows.
- 0051 must treat role/pathway taxonomy as a platform foundation layer.
- 0051 must include exact Cursor prompt, scripts, files, tests, and evidence.
- 0051 should start with planning/audit before broad implementation.

#### UX-CHECKPOINT-1 Decision

**B UX_CHECKPOINT_ACCEPTED_WITH_MINOR_LIMITATIONS_READY_FOR_0051**

- **UX-CHECKPOINT-1 outcome (2026-07-12):** Decision **B** — ready for **0051 planning** with watch items (shell overflow, PDF 4-family, Platform CORS, no Task model).

---

### 0051-F0 Universal Role & Pathway Taxonomy Planning

**Status:** Completed (docs-only planning/audit)  
**Type:** `PLANNING_AUDIT_ONLY` — no product-code implementation in F0  
**Date:** 2026-07-12  
**Preflight HEAD:** `52e4116592179a7e697a0b3f6ed4fff8720d8571` (`docs(product): record post-CV Roadmap UX checkpoint`)  
**Evidence:** `~/Desktop/CareerKundi_0051_F0_Taxonomy_Planning_Evidence.txt`

#### Why 0051 Exists

0051 creates a **platform foundation** for consistent role and pathway understanding across CV Builder, Roadmap, Job Search, Interview Packs, Study Materials, and future CareerKundi modules.

It should prevent hardcoded one-feature interpretations of roles — e.g. treating Roadmap as only Graduate Launch, or treating CV Builder role text as isolated freeform text with no shared meaning across features.

It should support **global, platform-wide career pathways** while remaining evidence-grounded and not overbuilding. External taxonomies (O*NET, ESCO, NIST NICE) are **reference patterns only** in this phase — not ingested datasets and not licensing obligations.

**UX-CHECKPOINT-1 facts used:** `READY_FOR_0051_WITH_WATCH_ITEMS`; CV Builder (15-template gallery, save/load, PDF 4-family); Roadmap (`/roadmap` + `/roadmaps`, generate/load/detail, skill-based tracking); watch items: PDF mapping, no Task model, shell overflow @390, Platform CORS, advanced roadmap engine future; old 004E and Auto Apply remain frozen.

#### Current Repository Role / Pathway Inventory

| Area | Verified File / Module | Current Role/Pathway Concept | Current Status | Risk | 0051 Opportunity |
|---|---|---|---|---|---|
| CV Builder | `frontend/src/pages/CVBuilderPage.tsx`; `backend/app/schemas/cv_builder.py`; `backend/app/api/routes/cv_builder.py`; `backend/app/agents/cv_builder/*` | Freeform `target_role_title` / `target_role_description`; optional `target_job_id`; `generation_mode=role_targeted`; studio templates | PARTIAL_EXISTING | Role text not shared with Roadmap/Job Search | Hook generate/tailor to CanonicalRole + provenance |
| Roadmap | `frontend/src/pages/RoadmapPage.tsx`; `backend/app/api/routes/roadmap.py`; `backend/app/schemas/roadmap.py`; `backend/app/agents/roadmap/*`; `backend/app/db/models/roadmap.py` | Freeform `target_role`; hardcoded `SAMPLE_ROLES`; UI pathway examples (skill gap / switch / graduate); `RoleTaxonomyAgent` + `graph_rag.get_skills_for_role` + `mock_data.infer_required_skills` fallback | PARTIAL_EXISTING / HARDCODED | Tech-skewed samples; LLM taxonomy can fail → mock skills; no PathwayType field | Map `target_role` → CanonicalRole; add PathwayType without Task model |
| Jobs / Job Search | `frontend/src/pages/JobSearchPage.tsx` (JobsPage.tsx **MISSING**); `backend/app/api/routes/job_search.py`; `backend/app/schemas/job_search.py`; `backend/app/agents/job_search/*` | Profile `job_title` / `seniority_level`; JD-driven packs; domain/archetype/intent inside job_search knowledge | PARTIAL_EXISTING | Role meaning local to compiler | Shared CanonicalRole + SkillCluster with packs |
| Interview Pack / Study Material | `backend/app/services/role_pack_library.py`; `backend/app/agents/job_search/knowledge/*`; `backend/app/tools/document_export.py` | Role packs by job title; skill domains; evidence slots | PARTIAL_EXISTING / HARDCODED | Curated packs ≠ universal taxonomy | Alias → pack routing; confidence labels |
| Dashboard | `frontend/src/pages/DashboardPage.tsx` | Shows `activeRoadmap.target_role` | EXISTING_VERIFIED | Display-only free text | Display canonical title + pathway type later |
| Profile | `frontend/src/pages/ProfilePage.tsx`; `backend/app/db/models/profile.py` | Profile `job_title` as career SoT for AI features | PARTIAL_EXISTING | No canonical role id | Profile ↔ RoleAlias mapping |
| Platform page | `frontend/src/pages/PlatformPage.tsx`; PF subjects/goals APIs | Subject + `goal_kind=career` goals — not occupation taxonomy | PARTIAL_EXISTING | CORS watch on subjects | PathwayGoal may link to subject goals later |
| Backend schemas | `cv_builder.py`, `roadmap.py`, `job_search.py` | Disjoint role fields (`target_role`, `target_role_title`, `job_title`) | PARTIAL_EXISTING | Drift across products | Shared taxonomy contract types |
| Backend models | `cv.py`, `roadmap.py`, job/profile models | String role fields; no taxonomy tables | PARTIAL_EXISTING | Migration temptation in F1 | Defer DB until F2+ approved |
| Backend agents | roadmap RoleTaxonomy; cv_builder; job_search knowledge; chatbot snapshot `active_target_role` | Per-agent role inference | HARDCODED / PARTIAL_EXISTING | Inconsistent inference | Registry + confidence ladder |
| Taxonomy-adjacent data | `backend/app/data/popular_roles_catalog.json`; `backend/app/data/seed_graph.py`; `backend/app/tools/graph_rag.py`; `backend/app/api/routes/role_packs.py` | Popular roles catalog; skill↔role graph seeds; graph RAG; role pack routes | PARTIAL_EXISTING | Fragmented “almost taxonomy” | Inventory into F1 contract; do not ingest O*NET/ESCO yet |
| Frontend types / API client | `frontend/src/types/api.ts`; `frontend/src/lib/api.ts` | `target_role`, `job_title`, optional `seniority` | PARTIAL_EXISTING | No shared taxonomy types | F3 type/API alignment |
| Tests | CVB/ROAD/job_search tests under `backend/tests`, frontend `*.test.tsx` | Feature-local contracts | EXISTING_VERIFIED | Cross-feature role mismatch untested | F7 cross-feature checkpoint |
| Docs/tracker | master plan §0051; live tracker | 0051 planned; F0 this slice | EXISTING_VERIFIED | — | Keep tracker short; plan lives here |

**Uncertain / VERIFY_IN_REPO:** exact production wiring of `role_packs` routes vs job_search compiler; full coverage of `popular_roles_catalog.json` consumers; any hidden pathway_type column (none found in roadmap schema — free text only).

#### External Taxonomy Reference Map

| Reference | Useful Concept | How 0051 Should Use It | Must Not Do Yet |
|---|---|---|---|
| O*NET | Occupation taxonomy; skills/tasks; job zones; related occupations | Shape CanonicalRole / Skill / SeniorityLevel fields; mapping inspiration | Ingest full dataset; claim official O*NET sync |
| ESCO | Occupations + skills pillars; skills–occupations matrix | Inspire SkillCluster ↔ CanonicalRole matrix | Full ESCO dump; EU licensing obligations without review |
| NIST NICE | Work roles + responsibility levels (cyber workforce) | Pattern for SeniorityLevel / EvidenceRequirement in specialized domains | Treat as global default for all careers |
| Anthropic / tool-use architecture | Schema-bounded tools; prompt caching for repeated instruction sets | Plan agent tools that call taxonomy registry; cache static contract text carefully | Over-cache stale role packs; unbounded tool loops |
| Internal CareerKundi evidence packs | Role packs, study/interview knowledge | First-class internal source with provenance | Present curated pack as verified external taxonomy |
| User profile / CV data | `job_title`, CV content, passport signals | `user_provided` / `profile_supported` / `document_supported` | Invent credentials from thin CV text |
| Job description data | Saved jobs, JD extractors | `job_description_supported` role/skill extraction | Overfit one JD as universal role definition |
| Roadmap skill data | Milestone/skill JSON progress | Feed SkillCluster progress without Task model | Require Task model for taxonomy |

**Wording lock:** 0051 uses external taxonomies as **reference patterns and mapping inspiration first**. **0051-F0 does not ingest** full external datasets. Future ingestion must consider licensing, storage, update cadence, and attribution.

#### Proposed Universal Taxonomy Contract

Docs-only contract (not implemented in F0). Proposed core entities:

`CareerDomain`, `RoleFamily`, `CanonicalRole`, `RoleAlias`, `SeniorityLevel`, `PathwayType`, `PathwayGoal`, `SkillCluster`, `Skill`, `EvidenceRequirement`, `RegionContext`, `IndustryContext`, `LearningDepth`.

| Entity | Purpose | Example Fields | Used By | Notes |
|---|---|---|---|---|
| CareerDomain | Top-level domain bucket | id, label, description, aliases, related_domains | All | Keep coarse in MVP |
| RoleFamily | Family within a domain | id, domain_id, label, aliases, example_roles | CV, Roadmap, Jobs | Bridges free text → family |
| CanonicalRole | Stable role identity | id, role_family_id, title, aliases, description, seniority_range, common_industries, common_skills, related_roles | All | Primary join key |
| RoleAlias | Map user/JD strings → canonical | alias, canonical_role_id, source, confidence, region_context | Resolve APIs | Preserve provenance |
| SeniorityLevel | Scope / depth indicators | id, label, indicators, expected_scope, evidence_depth | Profile, packs, CV | Align with profile.seniority_level later |
| PathwayType | Kind of career journey | id, label, description, applies_to, example_goals | Roadmap first | UI examples already hint these |
| PathwayGoal | Concrete user goal instance | id, pathway_type_id, target_role_id, source_context, goal_text | Roadmap, Platform goals | May link subjects later |
| SkillCluster | Grouped skills | id, label, domain_id, related_roles | Roadmap, study | Maps to roadmap skills blobs |
| Skill | Atomic skill | id, cluster_id, label, aliases, evidence_examples, tool_examples | Roadmap tracker, interview | No Task model required |
| EvidenceRequirement | What evidence is needed | id, applies_to, evidence_type, required_for, confidence_policy | Interview, CV, badges | Honesty gates |
| RegionContext | Geo caveats | id, label, examples, caveats | Mobility / public sector later | No visa guarantees |
| IndustryContext | Industry overlays | id, label, common_roles, common_compliance_or_tools | CV, jobs | VERIFY_WITH_OFFICIAL_SOURCE for licensing |
| LearningDepth | Content depth rules | id, level, explanation, content_depth_rules | Study materials | Budget/latency control |

#### Proposed Pathway Types

| Pathway Type | User Problem Solved | Example Inputs | Output Should Influence | Notes |
|---|---|---|---|---|
| Skill Gap Plan | Close gaps to a target role | Current skills, target role | Roadmap skills/milestones | Existing UI copy |
| Career Switch Plan | Transferable path into new family | Source role, target role | Gap + related roles | Honesty on unknowns |
| Graduate Launch Plan | First-role readiness | Degree/context, target role | Foundations milestones | Not the only pathway |
| Interview Preparation Path | Pack readiness | Job/role, evidence | Interview/study packs | Tie to job_search |
| Job Application Path | Apply with fit narrative | JD + profile | CV tailor + jobs queue | Future Safe Apply |
| Study Abroad / Education Path | Education mobility | Program interest, region | Education checklist | No outcome guarantees |
| Professional Certification Path | Cred planning | Target cert, role | Roadmap modules | VERIFY_WITH_OFFICIAL_SOURCE |
| Public Sector Path | Public hiring readiness | Jurisdiction, role | Compliance-aware plan | Official-source later |
| International Migration / Regional Readiness Path | Mobility readiness | Region, occupation | Checklist + caveats | No visa guarantees |
| Portfolio / Project Path | Build proof | Target skills | Project milestones | EvidenceRequirement |
| Promotion / Seniority Growth Path | Level-up in family | Current seniority, target | Seniority + evidence depth | Align SeniorityLevel |

**Safety/honesty:** Do not guarantee visa/job outcomes. Do not invent certifications or licensing requirements. Mark regulatory/licensing as `VERIFY_WITH_OFFICIAL_SOURCE` unless official-source lookup exists later.

#### Source of Truth and Confidence Model

| Source Type | Confidence | Allowed Use | User-Facing Label | Notes |
|---|---|---|---|---|
| user_provided | High | Direct display; primary input | Provided by you | Free-text role entry |
| profile_supported | High | Prefer over inference | From your profile | Profile.job_title |
| document_supported | Medium–High | CV/passport-backed claims | From your document | Need extract provenance |
| job_description_supported | Medium–High | JD-tailored outputs | From the job description | Saved job / posting |
| external_taxonomy_reference | Medium | Mapping hints only | Reference taxonomy | Not “verified occupation” |
| model_inferred | Low–Medium | Suggestions only | Suggested | Never as verified |
| fallback_default | Low | Last resort | Default | e.g. mock skill list |
| unknown | None | Explicit gap | Unknown | Prefer over fake certainty |

**Rules:** Never present model-inferred role/pathway as verified. Taxonomy mappings must preserve provenance. Generated plans must distinguish evidence-backed, profile-supported, suggested, and unknown.

#### Where 0051 Should Integrate

| Feature | Current State | 0051 Integration Point | Risk | First Implementation Slice |
|---|---|---|---|---|
| CV Builder | Freeform target role + templates | Resolve `target_role_title` → CanonicalRole; store alias provenance | CV regression | 0051-F4 |
| Roadmap | Freeform `target_role` + skill progress | PathwayType + CanonicalRole on generate; keep skills as progress units | Empty skills / UX copy drift | 0051-F5 |
| Jobs / Job Search | JD + profile titles | Shared role resolve before pack compile | Pack quality / 004E freeze | 0051-F6 |
| Interview Packs | Role pack library | Alias → pack; confidence labels | Frozen old 004E repair | 0051-F6 (hooks only; no 004E repair) |
| Study Materials | Domain classifiers | SkillCluster / LearningDepth | Generic content | 0051-F6 |
| Dashboard | Displays target_role | Canonical label when available | Cosmetic | After F5 |
| Profile | job_title string | Optional canonical_role_id later | Profile SoT conflicts | F3+ |
| Platform page | Subjects/goals | PathwayGoal link later | CORS watch | Deferred |
| Future Safe Apply | Frozen / future | Application path type | Scope creep | Not in 0051 ladder |
| Future Badges/Achievements | Separate | EvidenceRequirement hooks | Premature | Not in 0051 ladder |

#### 0051 Implementation Ladder

| Slice | Purpose | Allowed Scope | Not Allowed | Evidence Required |
|---|---|---|---|---|
| **0051-F1** Taxonomy Repo Inventory + Contract Files | Boundary: pure contract module + docs + pure tests | New taxonomy knowledge/contract module; schemas/types if needed; docs; pure contract tests | Broad CV/Roadmap rewiring; DB migration; external dataset ingestion; LLM changes; UI redesign | Contract tests green; decision `TAXONOMY_CONTRACT_BOUNDARY_READY_FOR_BACKEND_MVP` |
| **0051-F2** Backend Taxonomy Registry MVP | In-process registry resolve alias→canonical; seed from internal catalogs only | Registry service; seed from existing internal JSON/graph; API read endpoints if thin | Full O*NET/ESCO ingest; CV/Roadmap UI rewrite | Registry unit tests; sample resolve evidence |
| **0051-F3** Frontend Type/API Alignment | Types + api client for taxonomy reads | `api.ts` / types; thin UI optional display | Full gallery redesign; migrations | Typecheck/build |
| **0051-F4** CV Builder Taxonomy Hook | Optional resolve on role-targeted generate | Minimal CV payload fields + provenance | Template gallery redesign; PDF engine rewrite | CV regression tests |
| **0051-F5** Roadmap Taxonomy Hook | PathwayType + role resolve on generate; keep skill progress | Roadmap schema additive fields; UI select pathway type | Task model; specialized pathway engines | Roadmap regression + skill status |
| **0051-F6** Job Search / Interview Pack Taxonomy Hook | Shared resolve before pack/study | Thin hooks; confidence labels | Old 004E repair; Auto Apply repair | Pack smoke tests; freeze respected |
| **0051-F7** Browser-Tested Cross-Feature Taxonomy Checkpoint | End-to-end consistency | Browser journeys CV↔Roadmap↔Jobs role strings | New features | Desktop evidence + Decision A/B |

#### Proposed 0051-F1 Scope

**0051-F1** should create/prepare the taxonomy **contract boundary** with minimal product risk.

**Allowed likely files:**
- new backend taxonomy knowledge/contract module (if approved)
- backend schemas/types if needed for the contract only
- docs updates
- tests for pure taxonomy contract behavior

**Not allowed in F1:**
- broad CV Builder rewiring
- broad Roadmap rewiring
- database migration
- external dataset ingestion
- LLM generation changes
- UI redesign

**Suggested F1 decision target:** `TAXONOMY_CONTRACT_BOUNDARY_READY_FOR_BACKEND_MVP`

#### Risk Register

| Risk | Impact | Evidence | Mitigation | Target Slice |
|---|---|---|---|---|
| Taxonomy overbuild | Delay; unused entities | Large entity list vs MVP needs | F1 contract only; MVP subset in F2 | F1–F2 |
| Hardcoded role aliases | Inconsistent UX | `SAMPLE_ROLES`; role_pack_library; popular_roles_catalog | Central RoleAlias with source tags | F2–F5 |
| Global occupation dataset licensing/storage | Legal/storage cost | O*NET/ESCO size | Reference-only until explicit ingest slice | Post-F2 gate |
| Model-inferred roles as verified | Trust harm | RoleTaxonomy LLM path | Confidence ladder + UI labels | F1 contract → F4–F6 |
| CV Builder / Roadmap regressions | Break working UX | UX-CHECKPOINT-1 green paths | Additive hooks; regression tests | F4–F5 |
| Role/pathway mismatch across features | User confusion | Disjoint field names | Shared CanonicalRole id | F3–F7 |
| International/regulatory claims without official source | Legal/safety | Migration/cert pathway types | VERIFY_WITH_OFFICIAL_SOURCE; no guarantees | All |
| Cost/latency from long taxonomy prompts | Spend / slow generate | Large catalogs in prompts | Registry tools + selective context; prompt cache only for stable contract | F2+ |
| Prompt cache misuse / stale context | Wrong roles served | Cached packs | Versioned contract; short TTL for dynamic data | F2+ |
| Agent tool-use overreach | Unbounded calls | Future tool design | Schema-bounded tools; budgets | F2+ |

#### Watch Items From UX-CHECKPOINT-1

| Watch Item | Current Status | Impact on 0051 | Handling |
|---|---|---|---|
| CV PDF 4-family style mapping | Accepted limitation | F4 must not require new PDF families | Out of 0051 scope |
| Roadmap no Task model | By design | Skills remain progress units | F5 must not add Task model |
| Shell overflow at 390px | `SHELL_OVERFLOW_OBSERVED_USABLE` | Browser F7 may re-observe | Do not redesign shell in 0051 |
| Platform CORS watch | Subjects noise; page loads | Platform PathwayGoal deferred | Do not block taxonomy MVP |
| Old 004E frozen | Frozen | F6 hooks only; no pack repair campaign | Respect freeze |
| Old Auto Apply frozen | Frozen | Job Application Path type is planning-only | No Safe Apply work in 0051 |

#### 0051-F0 Decision

**B UNIVERSAL_TAXONOMY_PLAN_ACCEPTED_WITH_WATCH_ITEMS**

- Plan accepted; UX-CHECKPOINT-1 watch items and freezes carried forward.
- **Recommended next slice:** **0051-F1 Taxonomy Contract Boundary**
- Product code modified in F0: **NO**

---

### 0051-F1 Taxonomy Contract Boundary

**Status:** Completed  
**Type:** `BACKEND_CONTRACT_BOUNDARY`  
**Date:** 2026-07-12  
**Preflight HEAD:** `c01a1bee763cd9b9b158256e5594cf1539488d1d`  
**Evidence:** `~/Desktop/CareerKundi_0051_F1_Taxonomy_Contract_Boundary_Evidence.txt`

#### Contract Boundary Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| backend taxonomy package | Missing | Added `backend/app/taxonomy/` | EXISTING | Pure contract package |
| contract entities | Planned in F0 only | Pydantic models for core entities | Implemented (MVP subset) | Compact subset of F0 list |
| source/confidence model | Planned | `SourceType` + `ConfidenceLevel` + validators | Implemented | Blocks inferred/fallback as verified |
| pathway type enum | Planned | 11 `PathwayType` values | Implemented | Matches F0 pathway set |
| normalization helpers | Missing | `normalization.py` helpers | Implemented | Deterministic; no LLM |
| seed catalog | Missing | Tiny internal illustrative catalog | Implemented | Not external ingestion |
| import boundary | N/A | No FastAPI/SQLAlchemy/LLM imports | Verified by tests | Source inspection |
| tests | Missing | `tests/unit/test_taxonomy_contract_boundary.py` | 11 passed | Plus related filter green |
| feature integration | None | None | NONE | Explicitly out of F1 |
| external dataset ingestion | None | None | NONE | O*NET/ESCO/NIST not ingested |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `backend/app/taxonomy/__init__.py` | Added | Public exports | Contract boundary |
| `backend/app/taxonomy/contracts.py` | Added | Enums + entity models | Contract boundary |
| `backend/app/taxonomy/normalization.py` | Added | Deterministic helpers | Contract boundary |
| `backend/app/taxonomy/catalog.py` | Added | Tiny internal seed | Tests / illustration |
| `backend/tests/unit/test_taxonomy_contract_boundary.py` | Added | Contract unit coverage | Tests |
| `docs/product/careerkundi_master_build_plan.md` | Updated | Record F1 results | Docs |
| `docs/product/careerkundi_live_tracker.md` | Updated | Position → F1 done / F2 next | Docs |

#### Contract Entities Implemented

| Entity / Enum | Implemented | Purpose | Notes |
|---|---|---|---|
| SourceType | YES | Provenance ladder | 8 values from F0 |
| ConfidenceLevel | YES | User-facing confidence | Blocks unsafe verified claims |
| SeniorityLevel | YES | Seniority indicators | Includes unknown |
| PathwayType | YES | Pathway kinds | 11 values |
| CareerDomain | YES | Domain bucket | id/label/aliases |
| RoleFamily | YES | Family within domain | example_roles |
| CanonicalRole | YES | Stable role identity | seniority_range + skills |
| RoleAlias | YES | Alias → canonical | source + confidence |
| SkillCluster | YES | Skill grouping | domain-linked |
| Skill | YES | Atomic skill | evidence/tool examples |
| PathwayGoal | YES | Goal instance | pathway_type + role |
| TaxonomyMatch | YES | Resolve result shape | For future registry |

#### Boundary Rules Verified

| Boundary Rule | Result | Evidence | Notes |
|---|---|---|---|
| No database import | PASS | taxonomy source + unit test | No SQLAlchemy |
| No FastAPI route | PASS | No routes touched; import test | No APIRouter |
| No LLM client | PASS | Import marker test | No Gemini/OpenAI/Anthropic |
| No external dataset ingestion | PASS | Tiny internal seed only | No O*NET/ESCO/NIST |
| No frontend integration | PASS | No `frontend/src` changes | — |
| No CV Builder integration | PASS | Agents/routes untouched | — |
| No Roadmap integration | PASS | Agents/routes untouched | — |
| No Job Search integration | PASS | Agents/routes untouched | — |

#### Test Decision

**TAXONOMY_CONTRACT_TESTS_ADDED_AND_PASSING**

- Targeted: `tests/unit/test_taxonomy_contract_boundary.py` → **11 passed**
- Broader filter `taxonomy or roadmap or cv or export or studio_template` → **34 passed**

#### 0051-F1 Decision

**A TAXONOMY_CONTRACT_BOUNDARY_ACCEPTED_READY_FOR_0051_F2**

#### Recommended Next Slice

**Next slice: 0051-F2 Backend Taxonomy Registry MVP**

#### 0051-F2 Guardrails

- 0051-F2 may create the backend registry MVP around the contract boundary.
- 0051-F2 must not add database migrations by default.
- 0051-F2 must not ingest external datasets.
- 0051-F2 must not wire CV Builder/Roadmap/Job Search yet unless explicitly approved.
- 0051-F2 must preserve deterministic taxonomy behavior and test coverage.

---

### 0051-F2 Backend Taxonomy Registry MVP

**Status:** Completed  
**Type:** `BACKEND_REGISTRY_MVP`  
**Date:** 2026-07-12  
**Preflight HEAD:** `182663e4298ced264d4ec5fc65848fd476931400`  
**Evidence:** `~/Desktop/CareerKundi_0051_F2_Taxonomy_Registry_MVP_Evidence.txt`

#### Registry MVP Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| registry module | Missing | Added `backend/app/taxonomy/registry.py` | Implemented | In-memory only |
| seed catalog loading | Catalog only | `TaxonomyRegistry.from_seed_catalog()` | Implemented | Tiny internal seed |
| role id lookup | Missing | `get_role` | Implemented | Exact id |
| role title/alias match | Missing | `match_role` + normalized indexes | Implemented | No nearest-neighbor guess |
| skill id lookup | Missing | `get_skill` | Implemented | Exact id |
| skill label/alias match | Missing | `match_skill` | Implemented | Uses `matched_skill_id` |
| pathway validation | Enum only | `validate_pathway_type` / `list_pathway_types` | Implemented | Rejects invalid |
| role-to-skill lookup | Missing | `skills_for_role` | Implemented | Skips missing skill refs |
| related-role lookup | Field on role | `related_roles` | Implemented | Deterministic |
| source/confidence enforcement | F1 validators | Stricter + registry coercion | Implemented | No auto-verified |
| unknown/no-match behavior | N/A | Safe unknown match | Implemented | No hallucination |
| import boundary | F1 clean | Registry stays dependency-light | Verified | Tests cover markers |
| tests | Contract only | `test_taxonomy_registry.py` | Passing | + F1 still green |
| feature integration | None | None | NONE | Out of scope |
| external dataset ingestion | None | None | NONE | No O*NET/ESCO/NIST |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `backend/app/taxonomy/registry.py` | Added | In-memory registry MVP | Registry |
| `backend/app/taxonomy/__init__.py` | Updated | Export `TaxonomyRegistry` | Package |
| `backend/app/taxonomy/contracts.py` | Updated | Add `matched_skill_id` on `TaxonomyMatch` | Minimal contract |
| `backend/app/taxonomy/normalization.py` | Updated | Stricter verified bans + skill id kwarg | Confidence rules |
| `backend/tests/unit/test_taxonomy_registry.py` | Added | Registry unit coverage | Tests |
| `docs/product/careerkundi_master_build_plan.md` | Updated | Record F2 results | Docs |
| `docs/product/careerkundi_live_tracker.md` | Updated | Position → F2 done / F3 next | Docs |

#### Registry API Implemented

| Function / Method | Implemented | Purpose | Notes |
|---|---|---|---|
| `TaxonomyRegistry.from_seed_catalog` | YES | Load seed indexes | Classmethod |
| `get_role` | YES | Canonical role by id | None if missing |
| `get_skill` | YES | Skill by id | None if missing |
| `match_role` | YES | Title/alias/id match → `TaxonomyMatch` | Defaults inferred |
| `match_skill` | YES | Label/alias/id match → `TaxonomyMatch` | Sets `matched_skill_id` |
| `list_pathway_types` | YES | Enumerate pathway types | 11 values |
| `validate_pathway_type` | YES | Parse/validate pathway | Raises on invalid |
| `skills_for_role` | YES | Role → known seed skills | Skips absent refs |
| `related_roles` | YES | Role → related canonical roles | Empty if none |

#### Boundary Rules Verified

| Boundary Rule | Result | Evidence | Notes |
|---|---|---|---|
| No database import | PASS | taxonomy source + tests | No SQLAlchemy |
| No FastAPI route | PASS | No routes touched | No APIRouter |
| No HTTP client | PASS | Import marker test | No requests/httpx |
| No LLM client | PASS | Import marker test | No Gemini/OpenAI/Anthropic |
| No external dataset ingestion | PASS | Seed catalog only | — |
| No frontend integration | PASS | No `frontend/src` changes | — |
| No CV Builder integration | PASS | Agents untouched | — |
| No Roadmap integration | PASS | Agents untouched | — |
| No Job Search integration | PASS | Agents untouched | — |
| No API route exposure | PASS | No `api/routes` changes | — |

#### Test Decision

**TAXONOMY_REGISTRY_TESTS_ADDED_AND_PASSING**

- Targeted: contract + registry → **24 passed**
- Broader filter `taxonomy or roadmap or cv or export or studio_template` → **47 passed**

#### 0051-F2 Decision

**A TAXONOMY_REGISTRY_MVP_ACCEPTED_READY_FOR_0051_F3**

#### Recommended Next Slice

**Next slice: 0051-F3 Frontend Type/API Alignment Planning**

- 0051-F3 should still not wire CV Builder or Roadmap behavior unless explicitly approved.
- It should likely plan/prepare shared frontend/backend type expectations or a read-only API contract boundary first.

#### 0051-F3 Guardrails

- 0051-F3 must preserve CV Builder and Roadmap browser-tested flows.
- 0051-F3 must not create broad UI rewiring.
- 0051-F3 must not ingest external datasets.
- 0051-F3 must not add database migrations by default.
- 0051-F3 should keep taxonomy exposure read-only and contract-bound.

---

### 0051-F3 Frontend Type / API Alignment Planning

**Status:** Completed (docs-only planning/audit)  
**Type:** `FRONTEND_TYPE_API_ALIGNMENT_PLANNING`  
**Date:** 2026-07-12  
**Preflight HEAD:** `0d1da42baa464dd027d9f40a5210183af0b788d0`  
**Evidence:** `~/Desktop/CareerKundi_0051_F3_Frontend_Type_API_Alignment_Planning_Evidence.txt`

#### Why F3 Exists

0051-F1 created deterministic taxonomy contracts.  
0051-F2 created an in-memory backend registry MVP.  
0051-F3 plans the **safe API/type boundary** before exposing taxonomy to frontend or features.

The goal is to prevent accidental broad wiring into CV Builder, Roadmap, Job Search, or UI before contracts are stable. Product code is **not** changed in F3.

**Prompt-quality carry-forward (Design Fidelity Layer):** Future UI-impacting prompts must include exact layout contract, section order, visual hierarchy, spacing/proportion rules, desktop/tablet/mobile behavior, screenshot/browser comparison requirements, visual acceptance criteria, and an explicit instruction not to settle for functional-but-visually-weak UI. Reason: CV Builder became functional but did not fully match the earlier premium studio visual target. **Do not redesign CV Builder in F3.**

#### Current Backend Taxonomy Capability Inventory

| Capability | Current Verified Source | Current Status | Frontend/API Implication | Notes |
|---|---|---|---|---|
| contract entities | `backend/app/taxonomy/contracts.py` | EXISTING_VERIFIED | Need DTO schemas later | Domains/families/roles/skills/goals |
| SourceType | contracts.py | EXISTING_VERIFIED | Mirror as TS union/enum | 8 values |
| ConfidenceLevel | contracts.py | EXISTING_VERIFIED | Mirror as TS union/enum | Blocks unsafe verified |
| PathwayType | contracts.py | EXISTING_VERIFIED | List endpoint later | 11 values |
| TaxonomyMatch | contracts.py | EXISTING_VERIFIED | Core match DTO | Has `matched_role_id` + `matched_skill_id` |
| TaxonomyRegistry | `registry.py` | EXISTING_VERIFIED | Backend service for routes | In-memory seed only |
| role lookup | `get_role` | EXISTING_VERIFIED | GET `/roles/{id}` | None → 404 later |
| role title/alias match | `match_role` | EXISTING_VERIFIED | POST `/roles/match` | No nearest-neighbor |
| skill lookup | `get_skill` | EXISTING_VERIFIED | Optional later | Not required in first API set |
| skill label/alias match | `match_skill` | EXISTING_VERIFIED | POST `/skills/match` | Sets `matched_skill_id` |
| pathway validation | `validate_pathway_type` | EXISTING_VERIFIED | GET pathway-types | Rejects invalid |
| role-to-skill lookup | `skills_for_role` | EXISTING_VERIFIED | GET `/roles/{id}/skills` | Skips missing seed refs |
| related-role lookup | `related_roles` | EXISTING_VERIFIED | GET `/roles/{id}/related` | Deterministic |
| unknown/no-match behavior | registry match | EXISTING_VERIFIED | Explicit unknown DTO | Must not hard-fail UI |
| import boundary | taxonomy tests | EXISTING_VERIFIED | Keep API thin wrappers | No LLM/HTTP in registry |
| seed catalog only | `catalog.py` | EXISTING_VERIFIED | Responses must say internal seed | No O*NET claim |
| API exposure | routes | MISSING | F4 creates read-only routes | No taxonomy router yet |
| frontend type exposure | `types/api.ts` | MISSING | F5 adds TS + client | No taxonomy types yet |

#### Current Frontend API / Type Inventory

| Area | Verified File | Current Pattern | Taxonomy Alignment Need | Risk |
|---|---|---|---|---|
| api.ts client pattern | `frontend/src/lib/api.ts` | Named `*Api` objects over Axios `http` at `/api/v1` | Add `taxonomyApi` later (F5) | Premature feature calls |
| types/api.ts interfaces | `frontend/src/types/api.ts` | Manual `*Read` / request interfaces | Add Taxonomy* types (F5) | Manual sync drift |
| CV Builder types | GeneratedCVRead; cvApi | Freeform `target_role_title`; templates | Optional resolve later | Hook too early |
| Roadmap types | RoadmapRead; roadmapApi | Freeform `target_role` | PathwayType + match later | Hook too early |
| Job Search types | SavedJobRead; jobApi; InterviewPackRead | job_title / packs | Shared CanonicalRole later | 004E freeze |
| Profile types | ProfileRead; profileApi | `job_title` string | Alias map later | SoT conflicts |
| Platform types | PlatformSubject/Goal | Subjects/goals envelopes | PathwayGoal link deferred | CORS watch |
| Dashboard usage | DashboardPage | Displays roadmap `target_role` | Display-only until F11 | Cosmetic |
| error handling | ApiError + interceptor | `{error,code,message,details}` | Taxonomy errors → ApiError | Unknown ≠ failure |
| loading/empty states | Feature pages | Page-local | Match UX for no-match | Treat as soft empty |
| manual type sync risk | api.ts ↔ schemas | Hand-maintained | F4/F5 checklist + tests | Stale fields |

**Backend conventions (verified):** routers use `APIRouter(prefix=...)` + mount under `/api/v1`; auth via `Depends(get_current_user)`; DB via `Depends(get_db)` where needed; Pydantic `*Read` / request models; unversioned `/health` exists separately. Taxonomy API should follow `/api/v1/taxonomy` + auth by default; **no DB session required** for seed registry.

#### Proposed Read-Only Taxonomy API Contract

Plan only — **do not implement in F3**.

| Endpoint | Method | Purpose | Request | Response | Auth | Notes |
|---|---|---|---|---|---|---|
| `/api/v1/taxonomy/health` | GET | Registry availability + seed counts | — | `TaxonomyHealthRead` | Required (or intentionally public) | Not `/health`; no external coverage claim |
| `/api/v1/taxonomy/pathway-types` | GET | Allowed pathway types | — | `TaxonomyPathwayTypeRead[]` | Required | Labels/descriptions |
| `/api/v1/taxonomy/roles/match` | POST | Deterministic role match | `TaxonomyMatchRequest` | `TaxonomyMatchRead` | Required | Unknown explicit |
| `/api/v1/taxonomy/skills/match` | POST | Deterministic skill match | `TaxonomyMatchRequest` | `TaxonomyMatchRead` | Required | `matched_skill_id` |
| `/api/v1/taxonomy/roles/{role_id}` | GET | Canonical role detail | path id | `TaxonomyRoleRead` | Required | 404 if missing |
| `/api/v1/taxonomy/roles/{role_id}/skills` | GET | Seed skills for role | path id | `TaxonomyRoleSkillsRead` | Required | May be empty |
| `/api/v1/taxonomy/roles/{role_id}/related` | GET | Related seed roles | path id | `TaxonomyRelatedRolesRead` | Required | Deterministic |

**Rules:** read-only; no DB; no external calls; no LLM; no user writes; preserve source/confidence; never claim O*NET/ESCO/NIST coverage; unknown/no-match explicit (not guessed).

#### Proposed Backend Schema Contract

Plan only — **do not implement in F3**. Likely home: `backend/app/schemas/taxonomy.py` (F4).

| Schema | Purpose | Fields | Maps From | Notes |
|---|---|---|---|---|
| TaxonomyHealthRead | Health/counts | available, role_count, skill_count, pathway_type_count, catalog_kind=`internal_seed` | SEED_CATALOG | No external claim |
| TaxonomyPathwayTypeRead | Pathway enum DTO | id, label, description | PathwayType | Static labels OK |
| TaxonomyMatchRequest | Match input | input_text, source?, confidence? | Registry kwargs | Defaults inferred |
| TaxonomyMatchRead | Match output | input_text, normalized_text, matched_role_id, matched_skill_id, source, confidence, explanation | TaxonomyMatch | Preserve provenance |
| TaxonomyRoleRead | Role detail | id, title, aliases, description, common_skills, related_roles, source, confidence | CanonicalRole | source often seed/reference |
| TaxonomySkillRead | Skill detail | id, label, aliases, evidence_examples, tool_examples, source, confidence | Skill | — |
| TaxonomyRoleSkillsRead | Role→skills | role_id, skills[] | skills_for_role | — |
| TaxonomyRelatedRolesRead | Related roles | role_id, related_roles[] | related_roles | — |
| TaxonomyErrorRead | Error body | Align with platform ApiError | CareerkundiError | Optional if reuse global |

#### Proposed Frontend Type Contract

Plan only — **do not implement in F3**. Likely home: `frontend/src/types/api.ts` (F5).

| TypeScript Type | Purpose | Fields | Backend Schema | Notes |
|---|---|---|---|---|
| TaxonomySourceType | Provenance union | string literals | SourceType | Manual sync |
| TaxonomyConfidenceLevel | Confidence union | string literals | ConfidenceLevel | Never auto-verified |
| TaxonomyPathwayType | Pathway union | 11 literals | PathwayType | — |
| TaxonomyMatchRequest | Client POST body | input_text, source?, confidence? | TaxonomyMatchRequest | — |
| TaxonomyMatchRead | Match result | as API | TaxonomyMatchRead | Soft-handle unknown |
| TaxonomyRoleRead | Role card | as API | TaxonomyRoleRead | — |
| TaxonomySkillRead | Skill card | as API | TaxonomySkillRead | — |
| TaxonomyHealthRead | Health panel | as API | TaxonomyHealthRead | Dev/ops + smoke |

**Rules:** no registry internals; treat match as suggested unless source/confidence say otherwise; display unknown safely; never label model-inferred as verified.

#### Proposed Frontend API Client Contract

Plan only — **do not implement in F3**. Likely home: `taxonomyApi` in `frontend/src/lib/api.ts` (F5).

| Client Method | Backend Endpoint | Purpose | Caller Features Later | Notes |
|---|---|---|---|---|
| `taxonomyApi.health()` | GET `/taxonomy/health` | Smoke | F6 checkpoint | Read-only |
| `taxonomyApi.listPathwayTypes()` | GET `/taxonomy/pathway-types` | Pathway UI later | Roadmap F9/F10 | — |
| `taxonomyApi.matchRole(input)` | POST `/taxonomy/roles/match` | Resolve free text | CV/Roadmap later | Unknown soft |
| `taxonomyApi.matchSkill(input)` | POST `/taxonomy/skills/match` | Resolve skill text | Study/Roadmap later | — |
| `taxonomyApi.getRole(roleId)` | GET `/taxonomy/roles/{id}` | Detail | Hooks later | 404 handled |
| `taxonomyApi.getRoleSkills(roleId)` | GET `/taxonomy/roles/{id}/skills` | Skills list | Roadmap later | — |
| `taxonomyApi.getRelatedRoles(roleId)` | GET `/taxonomy/roles/{id}/related` | Related | Roadmap later | — |

**Rules:** read-only client; user-readable errors; **no feature hard-fail** on unknown match.

#### Future UI Design Fidelity Requirement

| Future UI Slice | Design Fidelity Requirement | Browser/Screenshot Requirement | Notes |
|---|---|---|---|
| CV Builder taxonomy hook | Exact layout for role-resolve affordance; preserve studio hierarchy | Desktop + 390px; before/after screenshots | Do not redesign whole studio in hook slice |
| Roadmap taxonomy hook | Pathway type + role resolve placement; progress skills unchanged | Desktop + 390px | No Task model |
| Job Search taxonomy hook | Soft resolve chips only; no pack rewrite | Smoke journey | 004E frozen |
| Profile taxonomy preferences | Compact preference row; profile SoT clear | Desktop + mobile | Optional later |
| Dashboard taxonomy widgets | One composition; no dashboard clutter | Desktop | Optional |
| Platform taxonomy page | Subjects/goals first; taxonomy read-only panel if any | CORS watch | Deferred |

**Rules:** every future UI prompt must include exact layout contract, responsive rules, visual acceptance checklist, and browser screenshot/checkpoint notes. Do not accept merely functional UI if it misses intended product design. **CV Builder premium studio mismatch is a planning lesson, not an F3 redesign.**

#### Feature Integration Guardrails

| Feature | Future Taxonomy Use | Not Allowed Yet | First Safe Hook Slice |
|---|---|---|---|
| CV Builder | Resolve `target_role_title` | Any UI/API hook in F3–F6 | F7 plan → F8 impl |
| Roadmap | PathwayType + `target_role` resolve | Wiring in F3–F6 | F9 plan → F10 impl |
| Job Search | Shared role match before packs | Pack/compiler rewrite | After F6; respect 004E freeze |
| Interview Packs | Alias → pack routing labels | 004E repair | Deferred / freeze |
| Study Materials | SkillCluster depth | Content rewrite | After API boundary |
| Profile | Optional canonical role id | Forced remapping | After F5 |
| Dashboard | Display canonical title | New widgets now | After F10/F11 |
| Platform | PathwayGoal link | CORS/page redesign | Deferred |
| Safe Apply future | Application path type | Any apply work | Frozen / future |
| Badges/Achievements future | EvidenceRequirement | Badge rewrite | Future |

**Rules:** F3 planning only. **F4 = read-only backend taxonomy API + schemas.** CV/Roadmap hooks wait until API/type boundary is browser/test verified (F6).

#### Proposed 0051 Implementation Ladder Update

| Slice | Status / Purpose |
|---|---|
| 0051-F0 Universal Role & Pathway Taxonomy Planning | Done |
| 0051-F1 Taxonomy Contract Boundary | Done |
| 0051-F2 Backend Taxonomy Registry MVP | Done |
| **0051-F3 Frontend Type / API Alignment Planning** | **Done (this slice)** |
| 0051-F4 Read-Only Backend Taxonomy API | Done |
| 0051-F5 Frontend Taxonomy API Client + Types | Done |
| 0051-F6 Browser-Tested Taxonomy API Checkpoint | Done |
| 0051-F7 CV Builder Taxonomy Hook Planning | Done |
| 0051-F8 CV Builder Taxonomy Hook Implementation | Done |
| 0051-F9 Roadmap Taxonomy Hook Planning | Done |
| 0051-F10 Roadmap Taxonomy Hook Implementation | Done |
| 0051-F11 Cross-Feature Taxonomy Checkpoint | Done (this slice) |

**Do not jump from F3 into CV Builder/Roadmap hooks.** Expose and verify the taxonomy API/type boundary first.

#### Risk Register

| Risk | Impact | Evidence | Mitigation | Target Slice |
|---|---|---|---|---|
| frontend/backend type drift | Broken client | Manual `types/api.ts` | F4/F5 paired schemas + tests | F4–F5 |
| taxonomy unknown treated as failure | UX breakage | Soft-empty needed | Explicit unknown contract | F4–F6 |
| model-inferred shown as verified | Trust harm | Confidence rules | UI labels + API preserve source | F5–F8 |
| feature hooks break CV Builder | Regress UX-CHECKPOINT | Freeform role fields | Plan→impl ladder; Design Fidelity | F7–F8 |
| feature hooks break Roadmap | Regress skill progress | No Task model | Additive PathwayType only | F9–F10 |
| API before source/confidence UX ready | Misleading UI | Match defaults inferred | F6 checkpoint before hooks | F4–F6 |
| external taxonomy overclaim | Legal/trust | Seed-only catalog | `catalog_kind=internal_seed` in health | F4 |
| manual types stale | Drift | Hand-maintained TS | Checklist + contract tests | F5 |
| visual UI mismatch from vague prompts | Weak product | CV Builder lesson | Design Fidelity Layer in UI prompts | F7+ |
| Platform CORS watch | Noisy Platform | UX-CHECKPOINT-1 | Do not block taxonomy API | Carry |
| shell overflow @390 | Usable but overflow | UX-CHECKPOINT-1 | Observe in F6/F11; no shell redesign | Carry |

#### 0051-F3 Decision

**B FRONTEND_TYPE_API_ALIGNMENT_PLAN_ACCEPTED_WITH_WATCH_ITEMS**

- Plan accepted; UX watch items + Design Fidelity Layer + manual type-sync risk carried forward.
- **Recommended next slice:** **0051-F4 Read-Only Backend Taxonomy API**
- Product code modified in F3: **NO**

#### 0051-F4 Guardrails

- 0051-F4 may add read-only FastAPI taxonomy routes + Pydantic schemas wrapping `TaxonomyRegistry`.
- 0051-F4 must not add database migrations or ORM models.
- 0051-F4 must not ingest external datasets.
- 0051-F4 must not wire CV Builder, Roadmap, Job Search, or frontend UI.
- 0051-F4 must preserve source/confidence and unknown/no-match semantics.
- 0051-F4 must not claim external taxonomy coverage.

---

### 0051-F4 Read-Only Backend Taxonomy API

**Status:** Completed  
**Type:** `READ_ONLY_BACKEND_API`  
**Date:** 2026-07-12  
**Preflight HEAD:** `fb41fd601631ab5f0e7a5791b12a03c292ad1e80`  
**Evidence:** `~/Desktop/CareerKundi_0051_F4_Read_Only_Backend_Taxonomy_API_Evidence.txt`

#### API Boundary Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| backend taxonomy schemas | Missing | `backend/app/schemas/taxonomy.py` | Implemented | DTO layer only |
| taxonomy router | Missing | `backend/app/api/routes/taxonomy.py` | Implemented | Read-only |
| router registration | Missing | `main.py` include under `/api/v1` | Implemented | prefix `/taxonomy` |
| health endpoint | Missing | GET `/api/v1/taxonomy/health` | Implemented | Public; `internal_seed` |
| pathway-types endpoint | Missing | GET `/pathway-types` | Implemented | 11 types |
| role match endpoint | Missing | POST `/roles/match` | Implemented | Deterministic |
| skill match endpoint | Missing | POST `/skills/match` | Implemented | Deterministic |
| role detail endpoint | Missing | GET `/roles/{role_id}` | Implemented | 404 via NotFoundError |
| role skills endpoint | Missing | GET `/roles/{id}/skills` | Implemented | Seed skills only |
| related roles endpoint | Missing | GET `/roles/{id}/related` | Implemented | Deterministic |
| auth decision | N/A | Health public; others `get_current_user` | Documented | Tests override auth |
| source/confidence preservation | Registry only | Match + seed DTOs | Preserved | Seed = suggested reference |
| unknown/no-match behavior | Registry | API returns unknown | Explicit | No nearest guess |
| external dataset ingestion | None | Flag false on health | NONE | — |
| DB/API write behavior | N/A | No writes | NONE | Match POSTs are read-only |
| feature integration | None | None | NONE | No CV/Roadmap/Jobs |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `backend/app/schemas/taxonomy.py` | Added | API DTO schemas | API boundary |
| `backend/app/api/routes/taxonomy.py` | Added | Read-only routes | API boundary |
| `backend/app/main.py` | Updated | Register taxonomy router | Registration |
| `backend/tests/unit/test_taxonomy_api.py` | Added | API unit/TestClient coverage | Tests |
| `docs/product/careerkundi_master_build_plan.md` | Updated | Record F4 | Docs |
| `docs/product/careerkundi_live_tracker.md` | Updated | Position → F4 done / F5 next | Docs |

#### API Contract Implemented

| Endpoint | Method | Implemented | Auth | Response Model | Notes |
|---|---|---|---|---|---|
| `/api/v1/taxonomy/health` | GET | YES | Public | TaxonomyHealthRead | No DB |
| `/api/v1/taxonomy/pathway-types` | GET | YES | Required | list[TaxonomyPathwayTypeRead] | 11 items |
| `/api/v1/taxonomy/roles/match` | POST | YES | Required | TaxonomyMatchRead | Read-only match |
| `/api/v1/taxonomy/skills/match` | POST | YES | Required | TaxonomyMatchRead | Read-only match |
| `/api/v1/taxonomy/roles/{role_id}` | GET | YES | Required | TaxonomyRoleRead | 404 if missing |
| `/api/v1/taxonomy/roles/{role_id}/skills` | GET | YES | Required | TaxonomyRoleSkillsRead | — |
| `/api/v1/taxonomy/roles/{role_id}/related` | GET | YES | Required | TaxonomyRelatedRolesRead | — |

#### Schema Contract Implemented

| Schema | Implemented | Purpose | Notes |
|---|---|---|---|
| TaxonomyHealthRead | YES | Availability + counts | `external_dataset_ingestion=false` |
| TaxonomyPathwayTypeRead | YES | Pathway enum DTO | id/label/description |
| TaxonomyMatchRequest | YES | Match input | Trimmed non-empty text |
| TaxonomyMatchRead | YES | Match output | role + skill ids |
| TaxonomyRoleRead | YES | Role detail | Seed provenance suggested |
| TaxonomySkillRead | YES | Skill detail | — |
| TaxonomyRoleSkillsRead | YES | Role→skills | — |
| TaxonomyRelatedRolesRead | YES | Related roles | — |
| TaxonomyErrorRead | YES | Documented error shape | 404 uses NotFoundError envelope |

#### Boundary Rules Verified

| Boundary Rule | Result | Evidence | Notes |
|---|---|---|---|
| No database import | PASS | Route uses registry only; no Session | User type for Depends only |
| No DB writes | PASS | No commit/flush/add | — |
| No external HTTP calls | PASS | Import marker test | — |
| No LLM client | PASS | Import marker test | — |
| No external dataset ingestion | PASS | health flag false | — |
| No frontend integration | PASS | No frontend changes | — |
| No CV Builder integration | PASS | Agents untouched | — |
| No Roadmap integration | PASS | Agents untouched | — |
| No Job Search integration | PASS | Agents untouched | — |
| No user data write | PASS | Read-only routes | — |

#### Test Decision

**TAXONOMY_API_TESTS_ADDED_AND_PASSING**

- Targeted: contract + registry + API → **38 passed**
- Broader filter `taxonomy or roadmap or cv or export or studio_template` → **61 passed**
- Auth test setup: `TestClient` + empty lifespan + `get_current_user` override (no Postgres)

#### 0051-F4 Decision

**A READ_ONLY_TAXONOMY_API_ACCEPTED_READY_FOR_0051_F5**

#### Recommended Next Slice

**Next slice: 0051-F5 Frontend Taxonomy API Client + Types**

#### 0051-F5 Guardrails

- 0051-F5 may add frontend TypeScript types and taxonomyApi client only.
- 0051-F5 must not add UI integration or feature hooks.
- 0051-F5 must not change CV Builder or Roadmap behavior.
- 0051-F5 must preserve backend API contract and tests.
- 0051-F5 should include browser/API smoke only if frontend build/client use requires it.

---

### 0051-F5 Frontend Taxonomy API Client + Types

**Status:** Completed  
**Type:** `FRONTEND_API_CLIENT_TYPES`  
**Date:** 2026-07-12  
**Preflight HEAD:** `b0ee616c38f13bea295f8bbad56a17db76211086`  
**Evidence:** `~/Desktop/CareerKundi_0051_F5_Frontend_Taxonomy_API_Client_Types_Evidence.txt`

#### Frontend Contract Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| frontend taxonomy types | Missing | Added to `types/api.ts` | Implemented | Mirrors F4 schemas |
| source/confidence unions | Missing | `TaxonomySourceType` / `TaxonomyConfidenceLevel` | Implemented | Exact backend strings |
| pathway type union | Missing | `TaxonomyPathwayType` | Implemented | 11 values |
| health response type | Missing | `TaxonomyHealthRead` | Implemented | — |
| match request/response types | Missing | Match request/read | Implemented | nullable ids |
| role/skill response types | Missing | Role/Skill/Skills/Related | Implemented | + TaxonomyErrorRead |
| taxonomyApi client | Missing | `taxonomyApi` in `lib/api.ts` | Implemented | 7 methods |
| API path alignment | N/A | Paths under `/taxonomy/...` | Aligned | BASE_URL already `/api/v1` |
| protected endpoint handling | N/A | JWT interceptor unchanged | OK | Health public; others need auth |
| feature integration | None | None | NONE | No page imports |
| UI behavior | Unchanged | No UI edits | NONE | Design Fidelity remains watch |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/types/api.ts` | Updated | Taxonomy TS types | Frontend contract |
| `frontend/src/lib/api.ts` | Updated | `taxonomyApi` client | Frontend contract |
| `frontend/tests/unit/api.test.ts` | Updated | Surface coverage for taxonomyApi | Existing vitest convention |
| `docs/product/careerkundi_master_build_plan.md` | Updated | Record F5 | Docs |
| `docs/product/careerkundi_live_tracker.md` | Updated | Position → F5 done / F6 next | Docs |

#### Type Contract Implemented

| Type | Implemented | Backend Schema | Notes |
|---|---|---|---|
| TaxonomySourceType | YES | SourceType enum | 8 literals |
| TaxonomyConfidenceLevel | YES | ConfidenceLevel enum | 7 literals |
| TaxonomyPathwayType | YES | PathwayType enum | 11 literals |
| TaxonomyHealthRead | YES | TaxonomyHealthRead | — |
| TaxonomyPathwayTypeRead | YES | TaxonomyPathwayTypeRead | description nullable |
| TaxonomyMatchRequest | YES | TaxonomyMatchRequest | optional source/confidence |
| TaxonomyMatchRead | YES | TaxonomyMatchRead | null ids |
| TaxonomyRoleRead | YES | TaxonomyRoleRead | — |
| TaxonomySkillRead | YES | TaxonomySkillRead | — |
| TaxonomyRoleSkillsRead | YES | TaxonomyRoleSkillsRead | — |
| TaxonomyRelatedRolesRead | YES | TaxonomyRelatedRolesRead | — |
| TaxonomyErrorRead | YES | TaxonomyErrorRead | Documented shape |

#### API Client Contract Implemented

| Client Method | Endpoint | Implemented | Notes |
|---|---|---|---|
| `taxonomyApi.health` | GET `/taxonomy/health` | YES | Public backend |
| `taxonomyApi.listPathwayTypes` | GET `/taxonomy/pathway-types` | YES | Auth required |
| `taxonomyApi.matchRole` | POST `/taxonomy/roles/match` | YES | Read-only POST |
| `taxonomyApi.matchSkill` | POST `/taxonomy/skills/match` | YES | Read-only POST |
| `taxonomyApi.getRole` | GET `/taxonomy/roles/{id}` | YES | — |
| `taxonomyApi.getRoleSkills` | GET `/taxonomy/roles/{id}/skills` | YES | — |
| `taxonomyApi.getRelatedRoles` | GET `/taxonomy/roles/{id}/related` | YES | — |

#### Boundary Rules Verified

| Boundary Rule | Result | Evidence | Notes |
|---|---|---|---|
| No page/component integration | PASS | grep pages/components | — |
| No CV Builder behavior change | PASS | No CV files touched | — |
| No Roadmap behavior change | PASS | No Roadmap files touched | — |
| No Job Search behavior change | PASS | No Job Search files touched | — |
| No backend changes unless documented | PASS | No backend dirty | — |
| No external dataset ingestion | PASS | N/A frontend | — |
| No localStorage persistence | PASS | No new storage keys | Existing JWT interceptor only |
| No UI changes | PASS | Pages/components untouched | — |

#### Test / Build Decision

**FRONTEND_TAXONOMY_TYPES_TESTS_ADDED_AND_PASSING**

- `npm run build` (tsc + vite): PASS  
- `vitest run tests/unit/api.test.ts`: 3 passed  
- Backend `taxonomy` tests: 38 passed  

#### 0051-F5 Decision

**A FRONTEND_TAXONOMY_CLIENT_TYPES_ACCEPTED_READY_FOR_0051_F6**

#### Recommended Next Slice

**Next slice: 0051-F6 Browser/API Taxonomy Boundary Checkpoint**

#### 0051-F6 Guardrails

- 0051-F6 should verify backend taxonomy API + frontend taxonomyApi contract.
- 0051-F6 may use a small non-UI smoke script or existing browser/runtime checks.
- 0051-F6 must not integrate taxonomy into CV Builder, Roadmap, or Job Search yet.
- 0051-F6 must preserve all CV Builder and Roadmap browser-tested flows.

---

### 0051-F6 Browser/API Taxonomy Boundary Checkpoint

**Status:** Completed  
**Type:** `BROWSER_API_BOUNDARY_CHECKPOINT`  
**Date:** 2026-07-12  
**Preflight HEAD:** `4bd7b486f8c404f510a13cb595348d36b15d63a6`  
**Evidence:** `~/Desktop/CareerKundi_0051_F6_Taxonomy_Browser_API_Boundary_Checkpoint_Evidence.txt`

#### Boundary Check Summary

| Area | Result | Evidence | Issue Found | Follow-Up |
|---|---|---|---|---|
| backend taxonomy contract | PASS | `contracts.py` + unit tests | None | — |
| backend registry | PASS | `registry.py` + unit tests | None | — |
| read-only taxonomy API | PASS | routes + TestClient tests | None | — |
| router/OpenAPI | PASS | `/api/openapi.json` lists 7 taxonomy paths | None | — |
| taxonomy health | PASS | curl `200` + `external_dataset_ingestion:false` | None | — |
| pathway types | PASS | API tests (11 types) | None | — |
| role match | PASS | API tests title/alias/unknown | None | — |
| skill match | PASS | API tests alias/unknown | None | — |
| role detail | PASS | API tests 200/404 | None | — |
| role skills | PASS | API tests | None | — |
| related roles | PASS | API tests | None | — |
| auth behavior | PASS | health public; pathway-types curl `401`; TestClient override for auth paths | None | — |
| frontend taxonomy types | PASS | `types/api.ts` | None | — |
| frontend taxonomyApi client | PASS | `lib/api.ts` 7 methods | None | — |
| frontend build | PASS | `npm run build` | None | — |
| frontend tests | PASS | `vitest tests/unit/api.test.ts` 3 passed | None | — |
| backend tests | PASS | 38 taxonomy unit tests | None | — |
| runtime smoke | PASS | curl health + OpenAPI on `:8001` | None | — |
| browser/API smoke if run | SKIPPED | `BROWSER_PROTECTED_TAXONOMY_SMOKE_SKIPPED_BACKEND_TESTS_COVER_AUTH` | None | Optional later |
| feature integration guard | PASS | No page/component taxonomy imports | None | — |
| external ingestion guard | PASS | health flag false; seed only | None | — |
| DB write guard | PASS | No commit/flush/add in taxonomy | None | — |

#### Fixes Applied

No product-code fixes were required in 0051-F6.

#### Boundary Stabilization Decision

**TAXONOMY_BOUNDARY_CHECKPOINT_PASSED_WITH_WATCH_ITEMS**

Watch items (non-blocking; not taxonomy boundary defects):

- Design Fidelity Layer required for future UI-impacting taxonomy hooks (CV Builder lesson).
- Shell overflow @390 usable; Platform CORS watch; CV PDF 4-family; Roadmap no Task model.
- Old 004E / Auto Apply remain frozen.
- Protected browser JWT smoke not run; covered by backend API auth tests + runtime 401 check.

#### Remaining 0051 Work

| Remaining Work | Target Slice | Notes |
|---|---|---|
| CV Builder Taxonomy Hook Planning | 0051-F7 | Planning-only; Design Fidelity Layer |
| CV Builder Taxonomy Hook Implementation | 0051-F8 | After F7 |
| Roadmap Taxonomy Hook Planning | 0051-F9 | Preserve skill progress; no Task model |
| Roadmap Taxonomy Hook Implementation | 0051-F10 | After F9 |
| Cross-Feature Taxonomy Checkpoint | 0051-F11 | After hooks |
| Future external taxonomy ingestion | post-MVP | Licensing/storage/attribution gate |

#### 0051-F6 Decision

**B TAXONOMY_BOUNDARY_CHECKPOINT_ACCEPTED_WITH_WATCH_ITEMS**

#### Recommended Next Slice (after F6; superseded by F7 Decision)

F6 recommended **0051-F7**. F7 is now Done — see **0051-F7 Decision** → **0051-F8**.

#### 0051-F7 Guardrails

- 0051-F7 must be planning-only for CV Builder taxonomy hook.
- 0051-F7 must not redesign CV Builder yet.
- 0051-F7 must include the user-approved Design Fidelity Layer for any later UI-impacting implementation.
- 0051-F7 must preserve CV Builder browser-tested save/load/export flows.
- 0051-F7 must define exact taxonomy hook points before implementation.

---

### 0051-F7 CV Builder Taxonomy Hook Planning

**Status:** Completed (docs-only planning/audit)  
**Type:** `CV_BUILDER_TAXONOMY_HOOK_PLANNING`  
**Date:** 2026-07-12  
**Preflight HEAD:** `ffeca771edc3fea57bb8cfd5d835384c695eed54`  
**Evidence:** `~/Desktop/CareerKundi_0051_F7_CV_Builder_Taxonomy_Hook_Planning_Evidence.txt`

#### Why F7 Exists

0051-F7 plans how CV Builder should later use the taxonomy boundary without breaking browser-tested CV Builder flows.

The goal is to let CV Builder understand and preserve a **canonical role match** for the user's target role context (saved-job title and/or freeform role text) while keeping current CV creation, template selection, save/load, and export behavior stable.

**Prior outcomes used:** CVB-F0…F5 Done (15-template gallery, save/load, template persistence, PDF 4-family export); UX-CHECKPOINT-1 Decision B; 0051-F0…F6 Done (taxonomy contract → registry → API → frontend client → boundary checkpoint with watch items). No CV/Roadmap/Job Search taxonomy integration yet.

#### Current CV Builder Capability Inventory

| Area | Verified File / Module | Current Behavior | Taxonomy Relevance | Risk |
|---|---|---|---|---|
| CV Builder route/page | `frontend/src/pages/CVBuilderPage.tsx` | Studio layout: header actions + gallery + preview + studio panel; `generation_mode: "profile"` on save | Hook host | Scope creep / visual clutter |
| template gallery | `CVTemplateGallery.tsx` | 15-template structural gallery | Must stay independent of taxonomy | Accidental coupling |
| template preview | `CVTemplatePreview.tsx` | Live preview from profile + template | No taxonomy dependency | Preview shrink if UI bolted on |
| studio panel | `CVBuilderStudioPanel.tsx` | Name, tone, sections, **optional target job** select + JD textarea | Natural Role Intelligence placement near target job | Generic admin look |
| save/load | CVBuilderPage + `cvApi` | Save Draft generate-or-update; load restores template via `_studio` meta | Must preserve optional taxonomy meta | Old CVs without meta |
| selected template persistence | `_studio` in `section_config` via `studio_template.py` | Gallery id persisted without DB column | Pattern for `_taxonomy` meta | Meta collision if careless |
| export PDF | `cvApi.downloadPdf` + export route | Maps studio template → 4 style families | Must work with/without taxonomy | Export regression |
| target role/title input | Studio panel target job; backend `target_role_title` for `role_targeted` | UI today: optional saved job, not freeform `target_role_title` | Match input = job title / future freeform | VERIFY_IN_REPO if F8 adds freeform |
| GeneratedCVRead type | `frontend/src/types/api.ts` | id, target_job_id, template, studio_template_id, section_config, rendered_content | No taxonomy fields yet | Type drift in F8 |
| cvApi client | `frontend/src/lib/api.ts` | list/generate/update/get/export/delete | Call taxonomyApi separately in F8 | Auth/latency |
| backend generate | `POST /cv-builder/generate` | Profile/role_targeted; injects studio template into section_config | Do not require taxonomy for generate | Blocking unknown match |
| backend list/get/patch | ownership-checked CRUD | Patch updates name/template/studio/sections | Persist taxonomy via section_config meta preferred | Ownership must stay |
| backend export | `GET /cv-builder/{id}/export` | PDF using studio/template mapping | No taxonomy required | PDF engine rewrite forbidden |
| section_config metadata | `_studio` reserved row | JSON list on `GeneratedCV` | Add `_taxonomy` sibling meta | Avoid DB migration |
| tests | CV studio/export unit tests | Contract coverage for templates/export | F8 adds taxonomy hook tests | Weak UI acceptance |

#### Current Taxonomy Boundary Available to CV Builder

| Taxonomy Capability | Available Now | CV Builder Use Later | Limitation |
|---|---|---|---|
| `taxonomyApi.matchRole` | YES | Resolve job title / role text → match | Auth required; advisory only |
| `taxonomyApi.getRole` | YES | Optional detail after match | 404 if unknown id |
| `taxonomyApi.getRoleSkills` | YES | Optional later enrichment | Not required for F8 MVP |
| `TaxonomyMatchRead` | YES | Drive Role Intelligence card | Never treat inferred as verified |
| `TaxonomyRoleRead` | YES | Display canonical title/aliases | Seed catalog only |
| `TaxonomySkillRead` | YES | Deferred | Don't clutter F8 |
| SourceType | YES | Show provenance label | No O*NET claim |
| ConfidenceLevel | YES | Show confidence label | Ban verified for inferred |
| unknown/no-match behavior | YES | Safe empty state | Must not block CV |
| protected endpoint auth | YES | Uses existing JWT interceptor | Auth failure must soft-fail UI |

#### Proposed CV Builder Taxonomy Hook User Flow

| Step | User Action / System Action | Taxonomy Behavior | UI Feedback | Data Stored |
|---|---|---|---|---|
| 1 | User selects optional target job (or future freeform role text) | Derive match input from job title / role text | No modal required | Pending match input |
| 2 | System offers non-blocking role match | `taxonomyApi.matchRole` (debounced) | Compact Role Intelligence card | Ephemeral UI state |
| 3 | Confident deterministic match | Show suggested canonical role + confidence | “Suggested role match” | Draft match fields |
| 4 | Unknown / no match | Continue without blocking | “No deterministic match found” | `matched_role_id: null` |
| 5 | User accepts suggestion or keeps freeform | Never overwrite text without accept | Accept / Keep freeform | `accepted_by_user` flag |
| 6 | Save / load CV | Persist freeform context + taxonomy meta | Restore card on load | `_taxonomy` in section_config |
| 7 | Template selection | Independent | Unchanged gallery/preview | Studio meta unchanged |
| 8 | Export PDF | Ignore taxonomy for layout | Export still works | No PDF rewrite |

**Rules:** Taxonomy is advisory; never overwrite role text without confirmation; never label inferred as verified; unknown must not block creation; older CVs without taxonomy meta must load.

#### Proposed Data Contract

| Data Field | Location Candidate | Purpose | Migration Needed? | Notes |
|---|---|---|---|---|
| freeform / target role text | `_taxonomy.target_role_text` | Preserve user/job title text | No | From job title or freeform |
| taxonomy_matched_role_id | `_taxonomy.matched_role_id` | Canonical id | No | null if unknown |
| taxonomy_normalized_text | `_taxonomy.normalized_text` | Debug/restore | No | From match |
| taxonomy_source | `_taxonomy.source` | Provenance | No | e.g. user_provided |
| taxonomy_confidence | `_taxonomy.confidence` | Confidence label | No | suggested/unknown/… |
| taxonomy_match_explanation | `_taxonomy.explanation` | Short reason | No | Seed match text |
| taxonomy_accepted_by_user | `_taxonomy.accepted_by_user` | Explicit accept | No | boolean |
| taxonomy_updated_at | `_taxonomy.updated_at` | Freshness | No | ISO string optional |

**Storage rule:** Prefer `section_config` meta namespace `_taxonomy` parallel to `_studio`. Avoid DB migration in F8. Old CVs default to no taxonomy metadata.

Recommended metadata shape (plan only — not implemented in F7):

```json
{
  "section_id": "_taxonomy",
  "enabled": true,
  "target_role_text": "Software Developer",
  "matched_role_id": "software_engineer",
  "normalized_text": "software developer",
  "source": "user_provided",
  "confidence": "suggested",
  "explanation": "Deterministic match from internal seed catalog.",
  "accepted_by_user": false,
  "updated_at": "2026-07-12T00:00:00Z"
}
```

#### Proposed Frontend Hook Points

| Frontend File | Future Change | Why | Risk | F8 Guardrail |
|---|---|---|---|---|
| `CVBuilderPage.tsx` | Orchestrate match call, persist/restore meta, soft-fail auth | Page owns save/load | Clutter header | Keep card in panel region |
| `CVBuilderStudioPanel.tsx` | Compact Role Intelligence UI near target job | Natural control area | Generic form look | Design Fidelity Layer |
| `CVTemplatePreview.tsx` | Usually no change | Preview stays dominant | Preview shrink | Do not inject taxonomy UI |
| `DefaultCVSelector.tsx` | Usually no change | Load versions only | Accidental wiring | No taxonomyApi |
| `CVTemplateGallery.tsx` | No change | Gallery independence | Coupling | Forbidden to call taxonomyApi |
| `frontend/src/lib/api.ts` | Already has taxonomyApi | Use existing client | Path drift | Do not invent endpoints |
| `frontend/src/types/api.ts` | Optional CV meta helpers / typed taxonomy blob | Type safety | Overbuild | Minimal types only |
| `feature-pages.css` | Compact card styles under studio tokens | Visual fidelity | Dashboard look | Match studio CSS variables |

**Rules:** Do not call taxonomyApi from gallery; template selection independent; keep taxonomy UI compact and advisory; do not redesign whole studio unless F8 explicitly includes polish scoped to the card.

#### Proposed Backend Hook Points

| Backend File | Future Change | Why | Risk | F8 Guardrail |
|---|---|---|---|---|
| `api/routes/cv_builder.py` | Optionally accept/pass through taxonomy meta in generate/patch via section_config | Persist without new columns | Required taxonomy | Taxonomy optional |
| `schemas/cv_builder.py` | Optional documented meta shape only if needed | Contract clarity | Schema churn | Prefer opaque JSON meta |
| `db/models/cv.py` | No change preferred | Avoid migration | Migration temptation | No migration by default |
| `agents/cv_builder/*` | No taxonomy registry call in F8 MVP | Keep generation stable | Engine rewrite | Forbidden unless later slice |
| `tools/document_export.py` | No change | Export independence | PDF break | Forbidden redesign |
| `tests/*` | Persist/restore meta + non-blocking unknown | Regression safety | Weak coverage | Add targeted tests |

**Rules:** Prefer no DB migration; do not call taxonomy from generation engine in F8; do not change PDF export; do not weaken ownership; do not require taxonomy for generate.

#### Design Fidelity Layer — Future CV Builder Taxonomy Hook

**Principle:** Do not settle for a functional but visually weak UI. The taxonomy hook must feel integrated into the premium CV Builder Studio, not bolted on as a generic admin form.

**Desktop visual contract**

1. Top hero/status region: clear title, short subtitle, save/export status — no clutter.  
2. Main studio workspace: polished template gallery; **dominant** CV preview; studio panel as controls.  
3. Taxonomy hook placement: near target job / role controls in the studio panel as a compact **Role intelligence** card/chip — not a new column. Show: original role text, suggested canonical role (if matched), source/confidence label, accept/keep-freeform, unknown safe state.  
4. Must not: shrink preview excessively; crush gallery; add debug metadata boxes; create dashboard-table feel; leave large empty whitespace.

**Tablet visual contract**

- Gallery and Role intelligence stack cleanly; preview remains readable; controls do not crush preview; Role intelligence appears before advanced actions.

**Mobile visual contract**

- No horizontal overflow in CV feature content; Role intelligence full-width; buttons stack/wrap; preview accessible below; no tiny unreadable taxonomy text. (Shell overflow @390 remains a known watch item outside F8 taxonomy card.)

**Visual acceptance checklist (F8 cannot pass on build/tests alone)**

- Card aligns with CV Builder Studio design language  
- No generic admin dashboard look  
- Intentional spacing and clear hierarchy  
- Preview remains dominant; gallery remains readable  
- Empty/unknown and accepted states look intentional/polished  
- Screenshot/browser notes included  

**Browser evidence requirement for F8**

- empty/no taxonomy; matched; unknown; accepted (if implemented); reload persistence; 390px; 768px; desktop  

#### Copy and Confidence Rules

| State | User-Facing Copy Direction | Must Not Say |
|---|---|---|
| matched suggested role | “Suggested role match: …” + confidence | “Verified role” / O*NET coverage |
| unknown/no match | “No deterministic match found. You can continue with your role text.” | Error that blocks save |
| accepted suggested role | “Using suggested role for this CV version.” | Job/visa guarantees |
| freeform role kept | “Keeping your role text.” | That taxonomy failed the CV |
| taxonomy unavailable | Soft: “Role suggestions unavailable right now.” | Crash / hard disable Save |
| older CV without taxonomy metadata | No card or empty advisory state | Forced rematch on load |

#### F8 Implementation Scope Recommendation

0051-F8 should implement a **small advisory** CV Builder taxonomy hook:

**Allowed**

- Call `taxonomyApi.matchRole` when target job title / role text is present (debounced).  
- Show compact Role Intelligence card in studio panel.  
- Preserve freeform / job title text.  
- Store optional `_taxonomy` metadata in `section_config` (no DB migration).  
- Restore taxonomy metadata on load.  
- Keep template selection and PDF export independent.  
- Soft-fail on auth/network taxonomy errors.  
- Add tests/build + Design Fidelity browser evidence.

**Not allowed**

- Full CV Builder redesign; template redesign; PDF engine redesign.  
- DB migration by default; external taxonomy ingestion.  
- Role-based generation engine rewrite; Roadmap/Job Search integration.  

F8 must include exact layout + browser screenshot acceptance requirements from this Design Fidelity Layer.

#### Risks and Mitigations

| Risk | Impact | Mitigation | Target Slice |
|---|---|---|---|
| CV generation blocked by unknown taxonomy | Breaks CVB flows | Advisory only; never gate Save/Generate | F8 |
| User role text overwritten | Trust loss | Accept/keep-freeform; no silent overwrite | F8 |
| Inferred shown as verified | Trust harm | Confidence labels; ban verified for inferred | F8 |
| Template selection tied to taxonomy | Gallery breakage | Gallery forbidden from taxonomyApi | F8 |
| Save/load meta breaks old CVs | Load failures | Default missing `_taxonomy` to empty | F8 |
| PDF export breaks | Regression | No export changes | F8 |
| UI cluttered/generic | Design miss | Design Fidelity Layer + screenshots | F8 |
| Visual result fails design target | User rejection | Visual checklist mandatory | F8 |
| Taxonomy API auth failure breaks CV page | Hard fail | Soft-fail card; CV continues | F8 |
| Frontend/backend type drift | Runtime bugs | Mirror F4/F5 contracts; tests | F8 |

#### 0051-F7 Decision

**B CV_BUILDER_TAXONOMY_HOOK_PLAN_ACCEPTED_WITH_WATCH_ITEMS**

- Plan accepted. Watch items: Design Fidelity mandatory for F8; PDF 4-family limit; shell overflow @390; Platform CORS; current UI uses target **job** more than freeform `target_role_title` (F8 should match on job title and optionally add minimal freeform later); 004E/Auto Apply frozen.  
- **Recommended next slice:** **0051-F8 CV Builder Taxonomy Hook Implementation**  
- Product code modified in F7: **NO**

#### 0051-F8 Guardrails

- 0051-F8 implements advisory Role Intelligence only; must not redesign the full CV Builder Studio.  
- 0051-F8 must include the Design Fidelity Layer and browser evidence checklist from F7.  
- 0051-F8 must preserve save/load/export and template independence.  
- 0051-F8 must not add DB migrations by default; prefer `_taxonomy` section_config meta.  
- 0051-F8 must soft-fail taxonomy API errors and never block CV creation on unknown match.

---

### 0051-F8 CV Builder Taxonomy Hook Implementation

**Status:** Completed  
**Type:** `CV_BUILDER_TAXONOMY_HOOK_IMPLEMENTATION`  
**Date:** 2026-07-12  
**Preflight HEAD:** `10b62f3f50acc0d51ac63d07eb13310bb684ddb9`  
**Evidence:** `~/Desktop/CareerKundi_0051_F8_CV_Builder_Taxonomy_Hook_Implementation_Evidence.txt`

#### Implementation Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| Role Intelligence card | Missing | Compact card in `CVBuilderStudioPanel` | PASS | Explicit “Check role match” |
| taxonomyApi.matchRole | Unused by CV | Called on check | PASS | Soft-fail → unavailable |
| taxonomy role detail lookup | N/A | Optional `getRole` after match | PASS | Falls back to role id |
| `_taxonomy` metadata | Missing | Reserved section_config row | PASS | Parallel to `_studio` |
| save/load persistence | Studio only | Generate/update inject/preserve taxonomy | PASS | API + browser verified |
| template independence | N/A | Gallery never calls taxonomyApi | PASS | Browser verified |
| export preservation | Existing PDF | No PDF redesign; export still works | PASS | API + browser download |
| unknown/no-match behavior | N/A | Safe unknown + keep wording | PASS | “Galactic Tea Router” |
| source/confidence copy | N/A | Suggested/unknown labels only | PASS | No “verified” claim |
| Design Fidelity Layer | Required by F7 | Studio-panel card + CSS tokens | PASS w/ watch | Compact; not admin form |
| responsive behavior | Studio known overflow | Card usable; shell overflow remains | WATCH | @390 / tablet overflow known |
| tests/build/browser | Pre-F8 green | Build + unit + browser journey | PASS | See decision |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/CVBuilderPage.tsx` | Modified | Orchestrate match/save/load taxonomy state | Allowed |
| `frontend/src/components/features/CVBuilderStudioPanel.tsx` | Modified | Role Intelligence UI | Allowed |
| `frontend/src/types/api.ts` | Modified | `CVTaxonomyMeta` / section config fields | Allowed |
| `frontend/src/lib/api.ts` | Modified | Pass optional `taxonomy` on generate/update | Allowed |
| `frontend/src/styles/feature-pages.css` | Modified | Role Intelligence card styles | Allowed |
| `backend/app/schemas/cv_builder.py` | Modified | Taxonomy meta helpers + request fields | Allowed (required for persist) |
| `backend/app/api/routes/cv_builder.py` | Modified | Inject/preserve `_taxonomy` on generate/update | Allowed |
| `backend/tests/unit/test_cv_studio_template_persistence.py` | Modified | Taxonomy meta roundtrip tests | Allowed |
| `docs/product/careerkundi_master_build_plan.md` | Modified | F8 record | Allowed |
| `docs/product/careerkundi_live_tracker.md` | Modified | Tracker | Allowed |

#### User Flow Verified

| Flow | Result | Evidence | Notes |
|---|---|---|---|
| empty state | PASS | Playwright | “Add a target role…” |
| suggested match | PASS | Playwright + API | Software Developer → software_engineer |
| accepted match | PASS | Playwright | “Using suggested role” |
| kept freeform | PASS | Playwright | After unknown |
| unknown match | PASS | Playwright | Galactic Tea Router |
| save/load | PASS | Playwright + API | Persist `_taxonomy` |
| template switch | PASS | Playwright | 15 templates; taxonomy kept |
| export | PASS | Playwright + API PDF bytes | Safe filename |
| mobile | PASS w/ watch | Playwright 390 | Card usable; shell overflow watch |
| tablet | PASS w/ watch | Playwright 768 | Overflow known from studio shell |
| desktop | PASS | Playwright 1440 | Preview + gallery present |

#### Boundary Rules Verified

| Rule | Result | Evidence | Notes |
|---|---|---|---|
| no required taxonomy | PASS | Save without taxonomy still works | Advisory only |
| no role overwrite without confirmation | PASS | Accept button required | Keep wording path |
| no verified claim for suggested match | PASS | Copy checklist | Confidence: suggested |
| no template dependency | PASS | Gallery unused taxonomyApi | |
| no PDF redesign | PASS | Export only | 4-family unchanged |
| no DB migration | PASS | section_config JSON meta | |
| no external taxonomy ingestion | PASS | Seed catalog only | |
| no Roadmap/Job Search integration | PASS | Scope guard | |

#### Test / Browser Decision

**CV_TAXONOMY_HOOK_BUILD_TEST_BROWSER_PASSING** (with responsive overflow watch items)

#### 0051-F8 Decision

**B CV_BUILDER_TAXONOMY_HOOK_ACCEPTED_WITH_WATCH_ITEMS**

- Hook accepted. Watch: shell/studio overflow @390 and tablet; PDF still 4 CSS families; Platform CORS; Design Fidelity remains a standing rule for future UI; 004E/Auto Apply frozen.  
- **Recommended next slice:** **0051-F9 Roadmap Taxonomy Hook Planning**

#### Recommended Next Slice (after F8; superseded by F9 Decision)

F8 recommended **0051-F9**. F9 is now Done — see **0051-F9 Decision** → **0051-F10**.

#### 0051-F9 Guardrails

- 0051-F9 must be planning-only for Roadmap taxonomy hook.  
- 0051-F9 must preserve Roadmap browser-tested flows.  
- 0051-F9 must include Design Fidelity Layer if any UI is later affected.  
- 0051-F9 must not integrate Roadmap until exact hook points are planned.

---

### 0051-F9 Roadmap Taxonomy Hook Planning

**Status:** Completed (docs-only planning/audit)  
**Type:** `ROADMAP_TAXONOMY_HOOK_PLANNING`  
**Date:** 2026-07-12  
**Preflight HEAD:** `627cbfbb2271582bd9dc3ac64a4f118476de6222`  
**Evidence:** `~/Desktop/CareerKundi_0051_F9_Roadmap_Taxonomy_Hook_Planning_Evidence.txt`

#### Why F9 Exists

0051-F9 plans how Roadmap should later use the taxonomy boundary without breaking the already browser-tested Roadmap feature (ROAD-F4 Decision B).

The goal is to let Roadmap understand the user’s target role, pathway direction, and optional skill hints with **deterministic taxonomy assistance**, while keeping generation, list/load, detail view, progress tracking, refresh, and delete behavior stable.

F9 is planning-only. **0051-F10** implements the hook if this plan is accepted.

**Prior outcomes used:** ROAD-F0…F4 Done (skill-status progress; no Task model; shell overflow @390 watch); 0051-F0…F8 Done (taxonomy API/client + CV Role Intelligence with `_taxonomy` pattern); UX-CHECKPOINT-1 Done; 004E/Auto Apply frozen.

#### Current Roadmap Capability Inventory

| Area | Verified File / Module | Current Behavior | Taxonomy Relevance | Risk |
|---|---|---|---|---|
| Roadmap route/page | `frontend/src/pages/RoadmapPage.tsx` | Hero + status strip + list + detail + skill tracker | Hook host | Clutter / design miss |
| generate form | Modal in RoadmapPage | `target_role`, pace, starting_skill_level, personalization_inputs | Natural Role Intelligence placement | Blocking generate |
| target role input | Generate modal `role` state | Freeform string → `roadmapApi.generate` | Match input | Silent overwrite |
| pathway/goal input | Pathway examples + freeform role | Examples are UX copy only | Optional pathway-type hint later | Confusing with PathwayType |
| roadmap list | List cards from `roadmapApi.list` | Select loads detail | Restore taxonomy meta on select | Old rows without meta |
| roadmap detail | Detail header + milestones | Shows target_role, pace, progress | Compact card near header/form | Shrink detail |
| milestones | Timeline/kanban views | Organize skills | Must stay dominant | Visual displacement |
| skill tracker | `SkillTracker` in page | Skills are progress units | Must not be replaced by taxonomy skills | Progress break |
| skill status update | `roadmapApi.updateSkillStatus` | not_started/in_progress/completed | Independent of taxonomy | Coupling |
| progress summary | Counts from `skill.status` | % complete skill-based | Must remain skill-based | Wrong progress source |
| refresh/regenerate | Skill refresh + roadmap regenerate | Regenerate replaces milestones/skills; passes personalization_inputs | Preserve `_taxonomy` unless role changes | Meta loss |
| delete | `roadmapApi.delete` | Ownership-checked | Unchanged | Accidental change |
| roadmapApi client | `frontend/src/lib/api.ts` | list/get/generate/regenerate/status/refresh/delete | Call taxonomyApi separately | Auth soft-fail |
| RoadmapRead type | `frontend/src/types/api.ts` | target_role, personalization_inputs, milestones/skills | No taxonomy fields yet | Type drift |
| backend generate | `POST /roadmap/generate` | Pipeline + persist ORM | Optional meta in personalization_inputs | Required taxonomy |
| backend list/get/delete | Ownership-checked | Eager milestones/skills | Load must tolerate missing meta | Ownership weaken |
| backend skill status | `PATCH .../skills/{id}/status` | Status only | No taxonomy | Scope creep |
| roadmap agent/fallback | `agents/roadmap/*` | Has **agent** `RoleTaxonomyAgent` (not 0051 API) | Do not conflate with taxonomyApi | Engine rewrite |
| tests | `test_roadmap_contract.py` | Contract coverage | F10 adds hook tests | Weak UI acceptance |
| responsive behavior | feature-pages.css + ROAD-F4 | Shell overflow @390 known | Card must not worsen | Overflow watch |

Status notes: most rows **EXISTING_VERIFIED**. Taxonomy UI **MISSING**. Safe storage candidate **EXISTING_VERIFIED** (`personalization_inputs` JSON). Agent RoleTaxonomy ≠ 0051 taxonomy (**VERIFY_IN_REPO** naming collision risk for F10 docs/code comments).

#### Current Taxonomy Boundary Available to Roadmap

| Taxonomy Capability | Available Now | Roadmap Use Later | Limitation |
|---|---|---|---|
| `taxonomyApi.matchRole` | YES | Resolve target_role text | Auth required; advisory |
| `taxonomyApi.getRole` | YES | Canonical title/aliases after match | Soft-fail to id |
| `taxonomyApi.getRoleSkills` | YES | Optional “suggested skills” chips | Never replace roadmap skills |
| `taxonomyApi.listPathwayTypes` | YES | Optional pathway label later | Seed pathway types only |
| `TaxonomyMatchRead` | YES | Drive Role Intelligence card | Never treat inferred as verified |
| `TaxonomyRoleRead` | YES | Display canonical title | Seed catalog |
| `TaxonomySkillRead` | YES | Optional suggestions | Not progress units |
| `TaxonomyPathwayType` | YES | Optional pathway context | Not required for F10 |
| SourceType | YES | Provenance label | No O*NET claim |
| ConfidenceLevel | YES | Confidence chip | Ban verified for suggested |
| unknown/no-match behavior | YES | Safe empty; continue generate | Must not block |
| protected endpoint auth | YES | JWT via existing client | Soft-fail UI |

#### Proposed Roadmap Taxonomy Hook User Flow

| Step | User/System Action | Taxonomy Behavior | UI Feedback | Data Stored |
|---|---|---|---|---|
| 1 | User enters target role in generate modal (or views existing roadmap) | Derive match input from freeform `target_role` | Compact Role Intelligence near form/header | Pending |
| 2 | User clicks “Check role match” (preferred; explicit) | `taxonomyApi.matchRole` | Loading state; controls stay usable | Ephemeral |
| 3 | Deterministic match | Optional `getRole` + `getRoleSkills` | Suggested role + confidence + optional skill chips | Draft meta |
| 4 | Unknown / no match | Continue | “No deterministic match found” | `matched_role_id: null` |
| 5 | Accept or keep freeform | Never overwrite without accept | Accept / Keep my wording | `accepted_by_user` / `kept_freeform` |
| 6 | Optional suggested skills | Advisory chips only | “Suggested skills from role intelligence” | `suggested_skill_ids` |
| 7 | Generate roadmap | Taxonomy optional | Generate works if unknown/unavailable | Persist meta in personalization_inputs if present |
| 8 | Skill tracker | Unchanged status logic | Tracker remains primary progress UI | RoadmapSkill rows only |
| 9 | Save/load (list/get) | Restore `_taxonomy` from personalization_inputs | Card restores | Nested JSON |
| 10 | Regenerate | Preserve taxonomy unless role text changes | Confirm dialog unchanged | Merge `_taxonomy` |
| 11 | Delete | Unchanged | Unchanged | Row deleted |

**Rules:** Advisory only; no overwrite without confirmation; never label suggested as verified; unknown must not block generation; older roadmaps without meta must load; progress remains skill.status-based.

#### Proposed Data Contract

| Data Field | Location Candidate | Purpose | Migration Needed? | Notes |
|---|---|---|---|---|
| freeform_target_role | `Roadmap.target_role` (+ meta mirror) | User wording | No | Canonical freeform column already exists |
| taxonomy_matched_role_id | `personalization_inputs._taxonomy.matched_role_id` | Canonical id | No | Preferred nest |
| taxonomy_normalized_text | `...normalized_text` | Restore/debug | No | |
| taxonomy_source | `...source` | Provenance | No | |
| taxonomy_confidence | `...confidence` | Confidence | No | |
| taxonomy_match_explanation | `...explanation` | Short reason | No | |
| taxonomy_accepted_by_user | `...accepted_by_user` | Explicit accept | No | |
| taxonomy_kept_freeform | `...kept_freeform` | Keep wording | No | |
| taxonomy_skill_suggestions | `...suggested_skill_ids` | Advisory skill ids | No | Not tracker rows |
| taxonomy_updated_at | `...updated_at` | Freshness | No | Optional ISO |

**Storage rule:** Prefer nesting under existing `personalization_inputs` JSON (`_taxonomy` key). **Avoid DB migration.** If F10 cannot safely merge on regenerate, keep first hook frontend-advisory and record persistence as follow-up — do not invent a migration by default.

Recommended metadata shape (plan only — not implemented in F9):

```json
{
  "_taxonomy": {
    "target_role_text": "Electrical Engineer",
    "matched_role_id": "electrical_engineer",
    "normalized_text": "electrical engineer",
    "source": "user_provided",
    "confidence": "suggested",
    "explanation": "Deterministic match from internal seed catalog.",
    "accepted_by_user": false,
    "kept_freeform": false,
    "suggested_skill_ids": ["load_calculations"]
  }
}
```

**Reuse note from F8:** CV stores `_taxonomy` as a reserved `section_config` row. Roadmap should **adapt** the pattern into `personalization_inputs._taxonomy` (object nest), not invent a fake milestone/skill row.

#### Proposed Frontend Hook Points

| Frontend File | Future Change | Why | Risk | F10 Guardrail |
|---|---|---|---|---|
| `RoadmapPage.tsx` | Role Intelligence in generate modal + optional detail header restore | Owns target_role UX | Clutter | Compact card; explicit Check button |
| `frontend/src/lib/api.ts` | Already has taxonomyApi; optional typed personalization merge | Client ready | Path drift | Do not invent endpoints |
| `frontend/src/types/api.ts` | Optional RoadmapTaxonomyMeta type | Type safety | Overbuild | Minimal types |
| `feature-pages.css` | Compact card styles under roadmap tokens | Design fidelity | Admin look | Match roadmap visual language |
| `DashboardPage.tsx` | **No F10 change** | Progress ring only | Scope drift | Forbidden taxonomyApi |

**Rules:** No taxonomyApi from Dashboard; generation must not depend on taxonomy; do not replace roadmap skills; do not hide skill tracker; keep UI compact; no full Roadmap redesign in F10.

#### Proposed Backend Hook Points

| Backend File | Future Change | Why | Risk | F10 Guardrail |
|---|---|---|---|---|
| `api/routes/roadmap.py` | Optionally merge/preserve `personalization_inputs._taxonomy` on generate/regenerate | Persist without migration | Meta wipe on regenerate | Preserve unless role changes |
| `schemas/roadmap.py` | Document optional `_taxonomy` nest; do not require it | Contract clarity | Schema churn | Opaque JSON preferred |
| `db/models/roadmap.py` | **No change preferred** | personalization_inputs already JSON | Migration temptation | No migration by default |
| `agents/roadmap/*` | **No 0051 registry call in F10 MVP** | Agent RoleTaxonomy is separate | Engine rewrite / naming confusion | Forbidden coupling |
| `tests/unit/test_roadmap_contract.py` | Persist/restore meta; unknown non-blocking | Regression | Weak coverage | Targeted tests |

**Rules:** Prefer no DB migration; do not call taxonomy registry from generation engine in F10; taxonomy not required; do not weaken ownership; do not change progress away from skill.status; do not change delete/refresh semantics.

#### Design Fidelity Layer — Future Roadmap Taxonomy Hook

**Principle:** Do not settle for a functional but visually weak UI. The Roadmap taxonomy hook must feel integrated into the Roadmap planning experience, not bolted on as a generic debug/admin form.

**Desktop visual contract**

1. Top planning/status region: clear title, target role/pathway context, generation/status feedback — no clutter.  
2. Main workspace: roadmap detail + milestones remain dominant; skill tracker remains visible/readable; taxonomy is compact and advisory.  
3. Placement: near generate target-role input and/or detail header as a compact **Role Intelligence** / **Pathway Intelligence** card/chip. Show: original target role, suggested canonical role, source/confidence, optional suggested skills, accept/keep-freeform, unknown safe state.  
4. Must not: shrink milestones excessively; hide/replace skill tracker; add full-width debug panel; look like raw API JSON; leave large empty whitespace; feel like an admin dashboard.

**Tablet visual contract**

- Card stacks cleanly above/beside controls; milestones readable; skill tracker usable; buttons wrap.

**Mobile 390px visual contract**

- No **new** horizontal overflow from the taxonomy card; full-width card; stacked actions; no tiny chips; skill tracker accessible; roadmap usable despite known shell overflow watch.

**Visual acceptance checklist (F10 cannot pass on build/tests alone)**

- Card aligns with Roadmap visual language; not admin/debug; intentional spacing; detail dominant; tracker visible; unknown/accepted/freeform intentional; screenshots/browser notes included.

**Browser evidence requirement for F10**

- empty; matched; unknown; accepted (if implemented); keep freeform; persistence if implemented; generate still works; skill status still works; delete still works; 390 / 768 / desktop; console/network.

#### Copy and Confidence Rules

| State | User-Facing Copy Direction | Must Not Say |
|---|---|---|
| matched suggested role | “Suggested role match: …” + confidence | “Verified role” / O*NET coverage |
| unknown/no match | “No deterministic match found. You can continue with your target role.” | Blocking error |
| accepted suggested role | “Using suggested role for this roadmap.” | Job/visa/career guarantees |
| freeform role kept | “Using your wording.” | Taxonomy failed the roadmap |
| taxonomy unavailable | “Role intelligence is unavailable right now. You can continue without it.” | Hard-disable Generate |
| older roadmap without taxonomy metadata | Empty/neutral advisory | Forced rematch |
| suggested taxonomy skills | “Suggested skills from role intelligence” | “Required skills” / replace tracker |

#### F10 Implementation Scope Recommendation

0051-F10 should implement a **small advisory** Roadmap taxonomy hook:

**Allowed**

- Call `taxonomyApi.matchRole` when target role text is present (explicit Check button preferred).  
- Optionally `getRole` / `getRoleSkills` after match for title + advisory skill chips.  
- Compact Role/Pathway Intelligence card in generate modal (+ restore on detail if meta exists).  
- Preserve freeform `target_role`.  
- Store optional `_taxonomy` under `personalization_inputs` if merge-safe; else frontend-advisory first and document persistence follow-up.  
- Generate/skill tracker/refresh/delete remain independent of taxonomy success.  
- Soft-fail taxonomy auth/network errors.  
- Tests/build + Design Fidelity browser evidence.

**Not allowed**

- Full Roadmap redesign; DB migration by default.  
- Replacing generated roadmap skills with taxonomy seed skills.  
- Changing progress calculation; Roadmap agent rewrite; wiring agent RoleTaxonomy to 0051 registry.  
- CV Builder changes; Job Search integration; Dashboard widget/taxonomy changes.  
- External taxonomy ingestion.

#### Risks and Mitigations

| Risk | Impact | Mitigation | Target Slice |
|---|---|---|---|
| Generation blocked by unknown taxonomy | Breaks ROAD-F4 | Advisory only; never gate Generate | F10 |
| User target role overwritten | Trust loss | Accept/keep-freeform | F10 |
| Inferred shown as verified | Trust harm | Copy rules; ban verified for suggested | F10 |
| Taxonomy skills replace roadmap skills | Tracker/progress break | Chips advisory only | F10 |
| Progress calculation broken | Feature regression | Keep skill.status source of truth | F10 |
| Regenerate loses metadata | Persistence miss | Merge `_taxonomy` unless role changes | F10 |
| Delete behavior changed | Regression | No delete logic change | F10 |
| UI cluttered/generic | Design miss | Design Fidelity Layer | F10 |
| Visual fails design target | User rejection | Screenshot checklist mandatory | F10 |
| Taxonomy auth failure breaks page | Hard fail | Soft-fail card | F10 |
| Frontend/backend type drift | Bugs | Mirror F4/F5 contracts | F10 |
| DB migration pressure | Scope creep | Use personalization_inputs | F10 |
| Shell overflow worsens | UX regression | Card full-width; no new overflow | F10 |
| Confusing agent RoleTaxonomy vs 0051 API | Wrong architecture | Document naming; no agent coupling | F10 |

#### 0051-F9 Decision

**B ROADMAP_TAXONOMY_HOOK_PLAN_ACCEPTED_WITH_WATCH_ITEMS**

- Plan accepted. Watch items: shell overflow @390; agent `RoleTaxonomyAgent` must stay decoupled from 0051 taxonomyApi; regenerate meta-merge care; PDF/CORS/CV design watches from prior slices; no Task model; 004E/Auto Apply frozen; Design Fidelity mandatory for F10.  
- **Recommended next slice:** **0051-F10 Roadmap Taxonomy Hook Implementation**  
- Product code modified in F9: **NO**

#### Recommended Next Slice

**Next slice: 0051-F10 Roadmap Taxonomy Hook Implementation**

#### 0051-F10 Guardrails

- 0051-F10 implements advisory Roadmap Role Intelligence only; must not redesign the full Roadmap page.  
- 0051-F10 must include the Design Fidelity Layer and browser evidence checklist from F9.  
- 0051-F10 must preserve generate/list/load/detail/skill status/refresh/delete and skill-based progress.  
- 0051-F10 must not add DB migrations by default; prefer `personalization_inputs._taxonomy`.  
- 0051-F10 must not call taxonomy registry from the Roadmap agent pipeline.  
- 0051-F10 must soft-fail taxonomy API errors and never block roadmap generation on unknown match.  
- 0051-F10 must not call taxonomyApi from Dashboard.

### 0051-F10 Roadmap Taxonomy Hook Implementation

**Type:** `ROADMAP_TAXONOMY_HOOK_IMPLEMENTATION`  
**Status:** Done (this slice)  
**Depends on:** 0051-F9 Decision B  

Implements the compact advisory **Role Intelligence** hook inside the existing Roadmap generate modal and restores accepted/freeform metadata on roadmap detail. Uses `taxonomyApi` only; persists under `personalization_inputs._taxonomy`. No DB migration. No coupling to `agents.roadmap.RoleTaxonomyAgent`.

#### Implementation Summary

| Area | Before | Change Made | Result | Notes |
|---|---|---|---|---|
| Role/Pathway Intelligence card | Absent | Compact card in generate modal + detail restore | PASS | Title: Role Intelligence |
| taxonomyApi.matchRole | Unused on Roadmap | Explicit “Check role match” | PASS | No keystroke spam |
| taxonomy role detail lookup | N/A | Optional `getRole` after match | PASS | Falls back to role id |
| taxonomy role skills lookup | N/A | Optional `getRoleSkills` advisory list | PASS | Not inserted into tracker |
| personalization_inputs._taxonomy metadata | Stripped by strict schema | Schema + dump by alias | PASS | No migration |
| generate/load persistence | No taxonomy | Nested `_taxonomy` on generate; restore on load | PASS | Older roadmaps OK |
| refresh/regenerate preservation | Would drop unknown keys | `_merge_personalization_on_regenerate` | PASS | Dropped when role changes |
| skill tracker independence | skill.status only | Unchanged | PASS | Advisory skills separate |
| progress preservation | skill.status | Unchanged | PASS | |
| delete preservation | Ownership delete | Unchanged | PASS | |
| unknown/no-match behavior | N/A | Soft continue copy | PASS | Never blocks generate |
| source/confidence copy | N/A | Suggested / user provided chips | PASS | No “verified” |
| Design Fidelity Layer | Planned in F9 | Roadmap-token card styling | PASS | Not admin/debug box |
| responsive behavior | Shell overflow @390 known | Card full-width; actions stack @430 | PASS | Shell overflow watch remains |
| tests/build/browser | F9 docs-only | Build + API + roadmap contract + browser | PASS | Decision B watch items |

#### Files Changed

| File | Change Type | Reason | Scope |
|---|---|---|---|
| `frontend/src/pages/RoadmapPage.tsx` | Feature | Role Intelligence UI + generate/detail wiring | Allowed |
| `frontend/src/types/api.ts` | Types | `RoadmapTaxonomyMeta` + `_taxonomy` on personalization | Allowed |
| `frontend/src/styles/feature-pages.css` | Style | `.roadmap-role-intelligence*` Design Fidelity | Allowed |
| `backend/app/schemas/roadmap.py` | Schema | `RoadmapTaxonomyMeta` + `_taxonomy` alias | Allowed |
| `backend/app/api/routes/roadmap.py` | Preserve | dump/merge helpers for regenerate | Allowed |
| `backend/tests/unit/test_roadmap_contract.py` | Test | Taxonomy accept/merge/decouple | Allowed |
| `docs/product/careerkundi_master_build_plan.md` | Docs | This section | Allowed |
| `docs/product/careerkundi_live_tracker.md` | Docs | Position → F11 | Allowed |

`frontend/src/lib/api.ts` and `frontend/tests/unit/api.test.ts` unchanged (existing `taxonomyApi` sufficient).

#### User Flow Verified

| Flow | Result | Evidence | Notes |
|---|---|---|---|
| empty state | PASS | Playwright | “Add a target role…” |
| suggested match | PASS | Playwright + API | Electrical Engineer |
| accepted match | PASS | Playwright | Use suggested role |
| kept freeform | PASS | Playwright | Keep my wording |
| unknown match | PASS | Playwright + API | Galactic Tea Router |
| generate | PASS | Playwright + HTTP 201 | `_taxonomy` persisted |
| load/detail | PASS | Playwright restored card | Compact detail card |
| skill status update | PASS | Playwright select → in_progress | Tracker unchanged shape |
| progress summary | PASS | Playwright | Still skill-based |
| refresh/regenerate | PASS | Playwright + API merge | Preserved when role same |
| delete | PASS | Playwright confirm dialog | Dismissed after prove |
| mobile | PASS | 390 card within viewport | Shell overflow watch |
| tablet | PASS | 768 no new overflow | |
| desktop | PASS | Balanced layout | |

#### Boundary Rules Verified

| Rule | Result | Evidence | Notes |
|---|---|---|---|
| no required taxonomy | PASS | Generate without meta still works | |
| no role overwrite without confirmation | PASS | Accept button only | |
| no verified claim for suggested match | PASS | Copy audit in browser | |
| no taxonomy skills replacing Roadmap skills | PASS | Advisory list only | |
| no progress calculation rewrite | PASS | skill.status unchanged | |
| no Roadmap agent coupling | PASS | Route source + contract test | |
| no Dashboard integration | PASS | Scope guard | |
| no DB migration unless documented | PASS | JSON personalization only | |
| no external taxonomy ingestion | PASS | Seed catalog API only | |
| no CV Builder changes | PASS | Allowed-file diff | |

#### Test / Browser Decision

**ROADMAP_TAXONOMY_HOOK_BUILD_TEST_BROWSER_PASSING**

#### 0051-F10 Decision

**B ROADMAP_TAXONOMY_HOOK_ACCEPTED_WITH_WATCH_ITEMS**

Watch items: shell overflow @390 (pre-existing; Role Intelligence card itself within viewport); agent `RoleTaxonomyAgent` remains decoupled from 0051 `taxonomyApi`; regenerate must continue to preserve `_taxonomy` unless target role changes; PDF 4-family / Platform CORS / 004E + Auto Apply remain frozen; Design Fidelity carried into F11 checkpoint.

#### Recommended Next Slice

**Next slice: 0051-F11 Cross-Feature Taxonomy Checkpoint**

#### 0051-F11 Guardrails

- F11 must verify CV Builder + Roadmap taxonomy hooks together.  
- F11 must confirm taxonomy metadata does not cross-contaminate features.  
- F11 must confirm CV Builder and Roadmap browser-tested flows still pass.  
- F11 must not start Job Search/Interview integration.  
- F11 must not redesign UI.  
- F11 should record remaining watch items before moving to the next planned task phase.

### 0051-F11 Cross-Feature Taxonomy Checkpoint

**Type:** `BROWSER_CHECKPOINT + CONTRACT_CHECKPOINT` (docs-only closeout)  
**Status:** Done (this slice)  
**Depends on:** 0051-F10 Decision B  

Evidence-backed verification across the complete 0051 taxonomy chain. No production feature code changed. No Job Search / Interview Pack taxonomy hooks. No UI redesign. No silent product repairs.

#### Purpose

Confirm phase 0051 can close: deterministic backend contracts + registry, read-only taxonomy API, frontend types/client, CV Builder Role Intelligence, Roadmap Role Intelligence, and cross-feature consistency/isolation.

#### F4–F10 implementation chain reviewed

| Slice | Commit | Scope |
|---|---|---|
| F4 Read-Only Backend Taxonomy API | `b0ee616c` | Routes + schemas + API tests |
| F5 Frontend Taxonomy API Client + Types | `4bd7b486` | `taxonomyApi` + types + unit test |
| F6 Taxonomy Boundary Checkpoint | `ffeca771` | Docs/evidence boundary closeout |
| F8 CV Builder Taxonomy Hook | `627cbfbb` | `section_config._taxonomy` Role Intelligence |
| F10 Roadmap Taxonomy Hook | `e05ccd0c` | `personalization_inputs._taxonomy` Role Intelligence |

#### Backend taxonomy result

PASS — contracts use typed enums/models; matching is deterministic; aliases normalize; unknown returns explicit unknown/no-match; no nearest-role fabrication; source/confidence guards prevent unsupported verified claims; seed catalog remains internal; no external dataset loading; registry independent of CV/Roadmap persistence.

#### API/client alignment result

PASS — seven read-only endpoints only (`health` public; others auth-required). No taxonomy mutation endpoints. Health reports `external_dataset_ingestion=false`. Frontend types mirror backend field names; seven `taxonomyApi` methods use correct paths with JWT interceptor. No separate taxonomy localStorage key.

#### CV Builder integration result

PASS — advisory Role Intelligence; explicit “Check role match”; suggestion does not overwrite role text; Accept vs Keep freeform distinct; unknown does not block save; metadata only under `section_config._taxonomy`; load/template change preserves meta; PDF export succeeds without requiring taxonomy; soft-fail does not block creation.

#### Roadmap integration result

PASS — advisory Role Intelligence in generate modal + compact detail restore; explicit check; no silent overwrite of `target_role`; unknown does not block generate; metadata only under `personalization_inputs._taxonomy`; same-role regenerate preserves `_taxonomy`; changed-role regenerate removes stale `_taxonomy`; suggested skills advisory only (not injected into tracker); progress remains `skill.status`-based; routes do not import `TaxonomyRegistry` or couple to `RoleTaxonomyAgent`; Dashboard not integrated.

#### Cross-feature consistency result

PASS — same input `Electrical Engineer` → both features resolve `matched_role_id=electrical_engineer` with compatible display title `Electrical Engineer`; source=`user_provided`, confidence=`suggested`.

#### Unknown/no-match result

PASS — `Galactic Tea Router` → explicit unknown in both features; freeform retained; CV save and roadmap generate not blocked; no verified claim.

#### Provenance/source/confidence result

PASS — UI shows honest source/confidence labels; seed role detail uses `external_taxonomy_reference` + `suggested`; match path preserves `user_provided`/`suggested` or `unknown`/`unknown`.

#### Metadata isolation result

PASS — CV stores only in `section_config._taxonomy`; Roadmap stores only in `personalization_inputs._taxonomy`; Roadmap ops did not mutate CV taxonomy/template; CV delete did not break Roadmap list; neither mutates the taxonomy registry.

#### Automated test results

| Suite | Result |
|---|---|
| Backend focused (5 files) | **65 passed** |
| Backend broader `-k "taxonomy or cv or export or studio_template or roadmap"` | **70 passed**, 17 deselected |
| Frontend `tests/unit/api.test.ts` | **3 passed** |
| Frontend `npm run build` | **PASS** |
| `frontend/dist` | ignored / unstaged |

#### Runtime/API result

PASS — local backend `:8001` (Docker `:8000` was stale without taxonomy routes); frontend `:5173`. Health 200; unauthenticated pathway-types 401; OpenAPI lists exactly the seven taxonomy endpoints (GET health, GET pathway-types, POST roles/match, POST skills/match, GET roles/{id}, GET roles/{id}/skills, GET roles/{id}/related). No taxonomy write endpoints.

#### Browser journey result

PASS — Playwright `channel: chrome` disposable user. Journey A (CV), Journey B (Roadmap), Journey C (isolation) executed. Role Intelligence selectors scoped by CV studio panel, generate dialog, and roadmap detail (no global ambiguous locator treated as product failure). Console errors: none. Page errors: none. Failed network requests: none.

#### Responsive result

PASS — Role Intelligence card stays within usable viewport at 1280×900, 768×1024, and 390×844; text readable; controls reachable; no card-specific overflow. Known app-shell horizontal overflow remains at tablet/mobile (watch item; not fixed in F11).

#### Runtime artifact hygiene result

PASS — `knowledge_graph.gpickle` mutated by roadmap generation; restored to committed HEAD bytes via atomic write (not `git restore`). Working tree clean of runtime artifact after cleanup. Backup at `~/Desktop/CareerKundi_0051_F11_Preflight_knowledge_graph_runtime_backup.gpickle`.

#### Remaining watch items

- App-shell horizontal overflow @390 (and observed @768) — do not expand into shell redesign here  
- PDF export remains four style families mapped from studio templates  
- Roadmap agent `RoleTaxonomyAgent` ≠ 0051 taxonomy API (intentional decoupling)  
- Platform CORS watch (non-blocking)  
- Design Fidelity Layer remains required for future UI slices  
- Old 004E Interview Pack repair and old Auto Apply remain frozen  
- Job Search / Interview Pack taxonomy hooks not started (deferred beyond 0051)

#### 0051-F11 Decision

**B TAXONOMY_CROSS_FEATURE_CHECKPOINT_ACCEPTED_WITH_WATCH_ITEMS**

- All product and contract requirements passed.  
- Phase **0051 Universal Role & Pathway Taxonomy** is accepted closed with carried watch items.  
- Product code modified in F11: **NO** (docs only).

**Next gate:** **0052 Career & Education Passport** — see **0052-F0** (this phase) → **0052-F1**.


### 0052-F0 Career & Education Passport Planning and Repository Audit

**Type:** `PLANNING_AUDIT_ONLY` (docs-only)  
**Status:** Done (this slice)  
**Depends on:** 0051 Decision B (taxonomy phase closed)  

#### 1. Purpose

Plan Career & Education Passport as CareerKundi’s durable, user-owned career and education record — not a renamed Profile page, not Claims & Evidence (0053), not a wallet, not a verification service, and not an AI biography.

Passport must organize personal/profile information, experience, education, projects, skills (with taxonomy references), thin credential references, career targets, lightweight provenance/status summaries, and reusable reads for CV Builder, Roadmaps, Opportunities, Education, and later features.

**Doctrine locks (carried):** `FEATURE ACCESS ≠ EVIDENCE STATUS`; user-stated data usable without evidence; `uploaded ≠ verified`; modular monolith; deterministic CRUD; no microservices; no god entity.

#### 2. Current repository inventory

| Area | State | Evidence |
|---|---|---|
| `/passport*` routes | **NONE** (planned only) | `App.tsx`; OpenAPI has no passport paths |
| `backend/app/career_passport/` | **MISSING** | package listing |
| `frontend/src/features/passport/` | **MISSING** | `frontend/src` has pages/, not features/ yet |
| Profile backend | **RICH EXISTING** | `db/models/profile.py` + `/api/v1/profile/*` section CRUD |
| Profile frontend | **THIN STUB / SCHEMA MISMATCH** | `ProfilePage.tsx` vs `ProfileUpdate`/`ProfileRead` |
| Platform subjects/goals | **EXISTING (PF11)** | `/platform` + `/api/v1/platform/subjects*` |
| Claims/provenance tables | **FOUNDATION EXISTING, NO PUBLIC API** | `career_claims`, `provenance_*`; internal services only |
| Taxonomy | **0051 CLOSED** | in-memory seed; advisory JSON refs |
| CV Builder / Roadmap | **STABILIZED** | read Profile (or skills); snapshots at generate |
| Passport DB tables | **NONE** | zero `passport` matches under `backend/app/db` |
| Prior Desktop evidence (0050/PF11/UX0/CVB/ROAD) | **MISSING on Desktop** at audit time | recorded honestly |

#### 3. Existing Profile ownership map

| Concern | Truth |
|---|---|
| Account identity | `users` (`User`: email, full_name, auth) |
| Profile | 1:1 `profiles.user_id` unique; created at registration |
| Sections | Relational children: `educations`, `work_experiences`, `projects`, `certifications`, `publications`, `languages`, `volunteer_entries`, `awards`, `references_`, `skills`, `custom_sections` (+ entries) |
| JSON fields | bullets/tags/technologies on rows; `other_social_links`, `interests` on Profile |
| Ownership | Auth JWT; section CRUD scoped to current user’s `profile_id` |
| API | `GET/PATCH /api/v1/profile`; `POST/PUT/DELETE /api/v1/profile/{section}…`; reorder; export; **import documented but not implemented** |
| Frontend | Manual save; **does not call section CRUD**; field names diverge (`summary` vs `bio_summary`, string skills vs skill rows, etc.) |
| Tests | **No dedicated Profile API/model tests** found |
| Completeness | `calculate_completeness_score()` weighted heuristic — must not become disclosure pressure in Passport |

**Critical planning fact:** Backend Profile is already a comprehensive CV Data Hub. Passport planning must reconcile with this schema — not invent a parallel empty model that ignores it.

#### 4. Platform Foundation relationship

| Concern | Truth | Passport rule |
|---|---|---|
| `/platform` | Subjects + goals foundation shell only | Do not absorb Platform UI |
| `CareerSubject` | Table `career_subjects`; multi-subject per user; **no biography** | Passport **references** `subject_id`; does **not** own Subject |
| Goals | `career_goals` subject-scoped | Lifecycle stays Platform; Passport Targets may optionally link later |
| Claims/provenance | Internal services + DB; **no public HTTP** | Consume later via 0053; do not reimplement |
| Privacy/geo | Foundation tables/services | Consume contracts later; do not reimplement |
| Local smoke (F0) | `GET /platform/subjects` returned **500** in one local probe | Watch: diagnose before hard subject dependency in F2/F3 |

#### 5. Taxonomy relationship

| Available | Notes |
|---|---|
| Seed roles | `software_engineer`, `electrical_engineer`, `clinical_pharmacist`, `project_manager` |
| Seed skills | `python`, `load_calculations`, `medication_safety`, `stakeholder_coordination` |
| Pathway types | 11 `PathwayType` values |
| Semantics | source/confidence guards; unknown explicit; advisory |
| Storage pattern | Persist **refs + meta** (IDs, source, confidence, acceptance) — never copy catalog objects |
| Freeform | Always allowed; taxonomy never silently overwrites user text |

#### 6. CV Builder relationship

| Fact | Implication |
|---|---|
| Generate/regenerate builds `_profile_snapshot()` from live Profile + User name/email | Passport must eventually supply equivalent snapshot shape |
| `rendered_content` is a **full copy** at generate time | Old CVs remain valid after Passport migration |
| Export reads saved CV only | No live Passport required for export |
| Gallery preview reads live `profileApi.get()` | Future: optional Passport read without breaking old CVs |
| `section_config._taxonomy` advisory | Independent of Passport skill rows |
| Must not auto-overwrite | CV edits never write Passport/Profile without explicit user action |

#### 7. Roadmap relationship

| Fact | Implication |
|---|---|
| `target_role` + `personalization_inputs` (+ `_taxonomy`) | Passport Targets may **prefill** generate form only |
| Progress = `roadmap_skills.status` | Passport must never mutate progress |
| Reads Profile skill **names** only | Optional future Passport skills read |
| Does not write Profile | Roadmap must not dump biography into Passport |
| Agent `RoleTaxonomyAgent` ≠ 0051 API | Keep decoupling |

#### 8. Achievement / credential terminology audit

| Term | Repo meaning | Passport treatment |
|---|---|---|
| Achievement (UI) | Label for **badge gallery** (`AchievementsPage`) | Non-owner; gamification stays badges |
| Badge | `badge_definitions` / `user_badges` progress metrics | Non-owner |
| Qualification | Job-extraction concept | Not a Passport entity |
| Certification (Profile) | `certifications` rows (`credential_id`, `credential_url`, …) | Map to thin **credential references** |
| Claim | `career_claims` (foundation) | 0053 owner |
| Evidence / source snapshot | `provenance_*` | 0053 owner |
| Verification | `VerificationStatus` axis | 0053 only; never auto-set in 0052 |

#### 9. Passport domain boundary

**Backend owner (preferred):** `backend/app/career_passport/` — matches master-plan §7.4 and existing package style (`platform/`, `taxonomy/`).  
**Frontend owner (preferred):** `frontend/src/features/passport/` — planned; today UI lives in `pages/` (ProfilePage is interim bridge).

| Concern | Passport owns | Reuses | Later owner | Explicit non-owner |
|---|---|---|---|---|
| Aggregate + sections CRUD | Yes | — | — | — |
| Subject identity | — | `CareerSubject` / identity service | — | Subject CRUD |
| Auth/login | — | auth | — | Auth |
| Taxonomy catalog | — | taxonomy API refs | — | Catalog contents |
| Claim verification | — | claim status enums (display) | 0053 | Verification workflows |
| Evidence bytes | — | optional `claim_id`/`source_id` later | 0053 | File storage |
| VC/wallet/DID | — | conceptual refs only | Later | Crypto/wallet |
| CV snapshots | — | read source for generate | CV Builder | Rendered CV ownership |
| Roadmap progress | — | prefills only | Roadmap | Skill status |
| Badges | — | — | Achievements | Gamification |
| Platform goals engine | optional target link | lifecycle | Platform | Goal CRUD UI |
| Public share platform | — | — | Later | Public URLs MVP |

#### 10. Conceptual entity model (no implementation in F0)

| Entity | Purpose | Phase |
|---|---|---|
| `CareerPassport` | Aggregate: owner, subject link, visibility, version | 0052 |
| Section ordering metadata | Display order / section prefs | 0052 |
| `PassportProfile` | Personal/headline/contact/summary view | 0052 — **prefer adapter over existing Profile top-level fields initially** |
| `PassportExperience` | Work history | 0052 — maps from `work_experiences` |
| `PassportEducation` | Education | 0052 — maps from `educations` |
| `PassportProject` | Projects | 0052 — maps from `projects` |
| `PassportSkill` | Skills + optional taxonomy_skill_id | 0052 — maps from `skills` |
| `PassportCredentialRef` | Thin credential/cert reference | 0052 MVP — maps from `certifications` |
| `PassportTarget` | Career targets / pathway prefs | 0052 MVP — new (not badges; not goals ownership) |
| Full Claim rows per field | — | **DEFER_0053** |
| Evidence attachments | — | **DEFER_0053** |
| Publications/languages/volunteer/awards/references/custom | Existing Profile sections | **OPTIONAL_0052 late / DEFER_LATER** (F6+ or post-MVP) |

**Aggregate strategy (RECOMMENDED_FOR_APPROVAL):**  
Passport becomes the **product SoT** via `career_passport` domain. Persistence F2 should **migrate/wrap existing Profile relational tables** rather than create a second parallel set of education/experience tables in the same release. Preferred sequence:

1. Introduce `career_passports` aggregate row (`owner_user_id`, optional `subject_id`, `visibility`, `version`).  
2. Reuse existing Profile child tables as section persistence for MVP (adapter), **or** migrate into passport-owned tables in one explicit F2 migration after contracts lock — **choose in F1/F2 with upgrade/downgrade tests**.  
3. Keep `/api/v1/profile` temporarily compatible (F7).  
4. Avoid dual-write drift: single write path through Passport services once F3 lands.

#### 11. Field classification (selected)

**CareerPassport**

| Field | Class |
|---|---|
| id, owner_user_id, created_at, updated_at | REQUIRED_0052 |
| subject_id | REQUIRED_0052 (nullable until default-subject resolver stable) |
| visibility (default private) | REQUIRED_0052 |
| version (optimistic concurrency) | OPTIONAL_0052 → RECOMMENDED |
| display_name / headline / summary | OPTIONAL_0052 (may mirror Profile/User) |
| public URL / org access | REJECT (MVP) / DEFER_LATER |

**Experience / Education / Project / Skill** — required identity + ownership + ordering; dates optional; grades optional; taxonomy refs optional; freeform labels required when no taxonomy match; no auto-verified.

**Credential reference** — thin fields only (`credential_type`, `title`, `issuer_name`, dates, identifier, url, status=`user_asserted` default, `source_type`). Crypto proofs / DID / wallet: **REJECT** for 0052.

**Target** — `target_role_text` required; `taxonomy_role_id` / `pathway_type` optional advisory; geography/seniority optional; never auto-accepted from AI.

#### 12. Claim / provenance boundary

Use independent axes already in platform claims (do not collapse):

| Axis | 0052 needs | 0053 |
|---|---|---|
| Origin / source_status (lightweight) | `user_asserted` / `unknown` / optional `suggested` (accepted) | Full `ClaimOrigin` |
| Support | Usually `not_provided` or `profile_supported` | `source_linked`, `evidence_backed`, … |
| Verification | Always treat as **unverified** for MVP display; never store `verified` via Passport CRUD | Verification workflows |

Recommended Passport field meta (lightweight, not full Claim row):

```text
source_status: user_asserted | suggested_accepted | unknown | not_provided
support_status: not_provided | profile_supported   # evidence_backed deferred
verification_status: unverified                    # fixed for 0052 writes
optional future: claim_id, source_id, snapshot_id
```

Rules: suggested taxonomy/AI never becomes owned without explicit accept; deleting evidence later must not erase underlying user claim (0053); credential ref ≠ verified credential.

#### 13. External interoperability references

| Standard | Adopt conceptually | Defer | Reject for 0052 MVP |
|---|---|---|---|
| W3C VC Data Model 2.0 | issuer/subject/claims/validity/status/format; authenticity ≠ claim truth; minimization | crypto, presentations, wallets, DIDs, selective disclosure, status registries | blockchain; calling uploads “VCs”; auto-trust issuer name |
| Open Badges / CLR | issuer/earner/achievement; criteria; evidence refs; skill alignment; longitudinal record | badge issuing, Badge Connect, signed credentials, CLR export | merging badges with Passport credentials |
| Europass concepts | structured education/qualification/portable profile | Europe-only UI; copy Europass chrome | geo lock-in |

Global-first regions: India, UAE/GCC, UK, Global Remote (+ future).

#### 14. API contract plan (not implemented)

**Recommended MVP family** (authenticated, owner-scoped, private default, no LLM, no evidence gate, no public share):

| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/passport` | Default aggregate (+ section summaries) |
| POST | `/api/v1/passport` | Lazy create if missing |
| PATCH | `/api/v1/passport` | Aggregate meta + version |
| GET/PATCH | `/api/v1/passport/profile` | Profile section |
| GET/POST | `/api/v1/passport/experiences` | List/create |
| GET/PATCH/DELETE | `/api/v1/passport/experiences/{id}` | Owned |
| GET/POST + item routes | `/api/v1/passport/education` | Same pattern |
| GET/POST + item routes | `/api/v1/passport/projects` | Same |
| GET/POST + item routes | `/api/v1/passport/skills` | Same |
| GET/POST + item routes | `/api/v1/passport/credentials` | Thin refs |
| GET/POST + item routes | `/api/v1/passport/targets` | Targets |

**MVP simplification allowed:** single aggregate GET with nested sections for first UI shell (F4), then split write endpoints (F3/F5). Prefer explicit section writes over silent nested PATCH of everything.

Hard rules: no client-supplied owner id; cross-user → 404 (match platform convention); empty lists not errors; unknown taxonomy → freeform retained; optimistic concurrency via `version` when present; structured errors; pagination deferred for early MVP (order_index lists).

Example (conceptual) match response field names must follow F1 contracts — do not invent at implementation time without F1.

#### 15. Route / navigation plan

Planned family (Career Core):

```text
/passport
/passport/profile
/passport/experience
/passport/education
/passport/projects
/passport/skills
/passport/credentials   # RECOMMENDED in MVP nav
/passport/targets
```

| Topic | Plan |
|---|---|
| `/profile` | Remain during transition; migrate UX toward `/passport/*` (F4–F7) |
| `/platform` | Stay foundation subjects/goals — not Passport |
| Save model | **Explicit save** for section forms (RECOMMENDED); optional later autosave |
| Completeness | Optional indicators only; no “100% required”; evidence never required |
| Mobile | Section nav + one job per screen; respect shell-overflow watch |

#### 16. Design Fidelity Layer (planning contract)

Personal professional portfolio feel; timeline for experience/education; clear section hierarchy; restrained completeness; no fake verified badges; no spreadsheet admin UI; no giant debug provenance panels; source/status visually secondary; polished empty states; accessible labels/focus/errors.

Viewport acceptance (future F4+): **1280×900**, **768×1024**, **390×844** — section cards usable; known shell overflow recorded, not fixed in Passport slices by default.

#### 17. Privacy / security plan

Defaults: `visibility=private`; sharing disabled; org access none; public URL none; AI context only when feature explicitly requests Passport read.

Risks: PII, education/employment sensitivity, credential identifiers, IDOR, mass assignment, log leakage, export leakage, future org access. Object-level ownership tests mandatory in F2/F3. No compliance completion claimed in F0.

#### 18. Migration / compatibility strategy

| Question | Answer |
|---|---|
| New tables required? | Likely `career_passports` (+ maybe section tables) — **decide in F1/F2** |
| Reuse Profile tables? | **Yes for MVP preferred** via adapter or one migration |
| Existing users | Lazy Passport create on first GET; backfill from Profile |
| Dual write | Avoid; single write path after F3 |
| Old Profile API | Temporary support through F7 |
| CV/Roadmap validity | Preserved (snapshots / independent progress) |
| Downgrade | Required if F2 adds migrations |
| Principle | **No migration until F1 contracts accepted** |

#### 19. Decision register

| # | Item | Class |
|---|---|---|
| 1 | Passport name “Career & Education Passport” | LOCKED_FROM_EXISTING_DECISION |
| 2 | Backend owner `career_passport/` | RECOMMENDED_FOR_APPROVAL |
| 3 | Frontend owner `features/passport/` | RECOMMENDED_FOR_APPROVAL |
| 4 | Reference `subject_id`; do not own Subject | RECOMMENDED_FOR_APPROVAL |
| 5 | Relationship with Profile: bridge → Passport SoT | RECOMMENDED_FOR_APPROVAL |
| 6 | Aggregate + wrap/migrate Profile tables | RECOMMENDED_FOR_APPROVAL |
| 7 | Lazy Passport creation on first access | RECOMMENDED_FOR_APPROVAL |
| 8 | Sections: profile, experience, education, projects, skills, credentials, targets | RECOMMENDED_FOR_APPROVAL |
| 9 | Credentials in MVP (thin refs) | RECOMMENDED_FOR_APPROVAL |
| 10 | Targets in MVP | RECOMMENDED_FOR_APPROVAL |
| 11 | Taxonomy refs advisory | LOCKED_FROM_EXISTING_DECISION |
| 12 | Freeform role/skill support | LOCKED_FROM_EXISTING_DECISION |
| 13 | Evidence optional / never access-gate | LOCKED_FROM_EXISTING_DECISION |
| 14 | Lightweight source/status meta | RECOMMENDED_FOR_APPROVAL |
| 15 | Public sharing | REJECT (MVP) / DEFER_LATER |
| 16 | Organization sharing | DEFER_LATER |
| 17 | Explicit save (not autosave) MVP | RECOMMENDED_FOR_APPROVAL |
| 18 | Section reordering | RECOMMENDED_FOR_APPROVAL (exists on Profile API) |
| 19 | Completion score | OPTIONAL — non-punitive only |
| 20 | Credential interoperability concepts only | RECOMMENDED_FOR_APPROVAL |
| 21 | AI-assisted summary | DEFER_LATER / REJECT auto-write |
| 22 | CV Builder read integration | DEFER to **0052-F7** |
| 23 | Roadmap prefill integration | DEFER to **0052-F7** |
| 24 | Claims/Evidence handoff | DEFER_TO_0053 |
| 25 | Migration approach details | VERIFY_IN_REPO in F1/F2 |
| 26 | Deletion/retention | RECOMMENDED private delete; retention DEFER with privacy foundation |
| 27 | Optimistic concurrency `version` | RECOMMENDED_FOR_APPROVAL |
| 28 | Mobile/nav Career Core | LOCKED_FROM_EXISTING_DECISION |
| 29 | Publications/volunteer/etc. in first MVP | DEFER_LATER (post F6 or later) |
| 30 | Repair Platform subjects 500 before subject hard-dep | VERIFY_IN_REPO (watch) |

No Decision-C blockers: recommendations are sufficient to start F1 contracts without forcing irreversible product choices (F1 is still docs/contracts-only).

#### 20. 0052 implementation ladder

| Slice | Type | Scope | Must not |
|---|---|---|---|
| **0052-F0** | PLANNING_AUDIT | This slice | Product code |
| **0052-F1** | CONTRACT_BOUNDARY | `career_passport` package; Pydantic/domain contracts; enums; validation; pure tests; no routes/DB writes | UI, migrations, claims |
| **0052-F2** | PERSISTENCE | Models + Alembic foundation migration; ownership; Profile compatibility; upgrade/downgrade tests | Frontend |
| **0052-F3** | API_MVP | Auth CRUD; ownership; section endpoints; errors; API tests | UI, LLM, evidence |
| **0052-F4** | FRONTEND_SHELL | `/passport` overview; nav; L/E/E; Design Fidelity | Full section editors (unless tiny) |
| **0052-F5** | EDITING | Profile + Experience + Education CRUD; dates; reorder; browser | Claims, wallet |
| **0052-F6** | EDITING | Projects, Skills, Credentials, Targets; taxonomy refs; freeform | Verification, evidence graph |
| **0052-F7** | COMPAT_INTEGRATION | Profile shim; CV/Roadmap optional Passport read; no silent overwrites | Broad rewrites |
| **0052-F8** | CHECKPOINT | Full browser/API/privacy/responsive phase close | New features |

#### 21. Risk register

| Risk | Failure mode | Mitigation | Target |
|---|---|---|---|
| God domain | Owns claims/CV/goals | Boundary table | F0/F1 |
| Duplicate Profile truth | Profile ≠ Passport | Single write path; F7 shim | F2/F7 |
| FE Profile stub drift | Users think Profile works fully | Passport UI replaces stub | F4–F5 |
| “Verified” credential | False trust | Thin refs + unverified default | F1/F6 |
| Evidence mandatory | Locked features | Doctrine lock | All |
| AI biography | Invented facts | No auto AI writes | F3+ |
| Cross-user access | PII leak | Ownership tests | F2/F3 |
| Taxonomy overwrite | Lost wording | Advisory + accept | F5/F6 |
| Migration damage | Broken CV/Profile | Upgrade/downgrade + compat | F2 |
| Public share leak | Overshare | Private default | F0/F4 |
| Admin UI | Weak UX | Design Fidelity | F4+ |
| Completion pressure | Over-disclosure | Optional sections | F4 |
| Credential scope balloon | Wallet complexity | Interop concepts only | F0/F6 |
| Claims duplication | Fight 0053 | Thin refs | F0/F1 |
| Shell overflow | Unusable forms | Layout contract | F4+ |
| Platform subjects 500 | Block subject link | Watch; nullable subject_id | F2/F3 |
| No Profile tests | Regressions | Add with F2/F3 | F2/F3 |

#### 22. Future testing / browser plan

Contract, persistence, API, frontend, and browser journeys as specified in F0 prompt §24 — owned by F1–F8. Cross-user isolation via API tests. Responsive 1280/768/390. CV and Roadmap isolation required at F7/F8.

#### 23. Watch items

- App-shell overflow @390/@768  
- Profile frontend ↔ backend schema mismatch  
- Missing Profile automated tests  
- Platform subjects list local 500 during F0 smoke  
- PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API  
- 004E / Auto Apply frozen  
- Job Search/Interview taxonomy not in 0052  
- Desktop prior-evidence files missing at audit time  

#### 24. 0052-F0 Decision

**B PASSPORT_PLAN_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F1**

- Repository ownership understood; domain boundary clear; ladder bounded.  
- Non-blocking watch items remain (Profile stub, subjects smoke, shell overflow).  
- Product code modified in F0: **NO**.

#### 25. Exact next slice

**Next slice: 0052-F1 Passport Contract Boundary**

#### 0052-F1 Guardrails

- Create `backend/app/career_passport/` contracts/enums/validation + pure tests only.  
- Do not add FastAPI routes, migrations, or frontend.  
- Do not invent claim verification or evidence requirements.  
- Preserve Profile compatibility strategy from this F0 plan.  
- Do not reopen 004E / Auto Apply / Job Search taxonomy.

### 0052-F1 Passport Contract Boundary

**Type:** `CONTRACT_BOUNDARY`  
**Status:** Done (this slice)  
**Depends on:** 0052-F0 Decision B  

#### Purpose

Pure Passport vocabulary: Pydantic contracts, enums, validation, Profile-compatible field names, advisory taxonomy references, and lightweight record-status axes. No persistence, routes, services, frontend, AI, or evidence handling.

#### Files created

| Path | Role |
|---|---|
| `backend/app/career_passport/__init__.py` | Public exports |
| `backend/app/career_passport/contracts.py` | Domain contracts |
| `backend/tests/unit/test_passport_contract_boundary.py` | Boundary tests |

#### Contract package boundary

Dependency-light; importable without app startup. Permitted: `pydantic`, stdlib, `app.taxonomy.contracts`, `app.taxonomy.normalization`, `app.platform.claims.status`. Forbidden: FastAPI, SQLAlchemy, `app.db`, `app.api`, `app.schemas`, LLM providers.

#### Enums

Passport-owned: `PassportVisibility` (private only), `PassportSectionKey` (7), `PassportSourceStatus`, `PassportTaxonomyKind`, `PassportCredentialType`.  
Reused: `PathwayType`, `SeniorityLevel`, `SourceType`, `ConfidenceLevel`, `SupportStatus`, `VerificationStatus`.

#### Record-status rules

`PassportRecordMeta` defaults to user_asserted / not_provided / unverified. Verification locked to `unverified`. Support limited to `not_provided` | `profile_supported`. No evidence-backed / verified / assessment axes in 0052 writes. No silent axis upgrades.

#### Taxonomy-reference rules

`PassportTaxonomyReference` keeps freeform `input_text`; optional `taxonomy_id`; normalizes text; validates ID shape and source/confidence; unknown ⇒ unknown/unknown; acceptance requires ID; kind must match field (role vs skill); no registry membership check in F1.

#### Profile compatibility mapping

Preserved field names for Profile, Experience, Education, Project, Skill, Certification/credential shapes. Passport adds only contract metadata (`record_meta`, taxonomy refs, `credential_type`, targets, section prefs).

#### Aggregate contract

`CareerPassportContract`: nullable `subject_id`, private visibility, `version >= 1`, default section order, empty sections valid, no owner/public/org/claims/evidence/CV/roadmap fields.

#### Validation matrix

Required nonblank strings; optional blank → None; date order; current ⇒ no end_date; priority 1–5; order_index ≥ 0; list trim/dedupe; duplicate section prefs rejected; extra fields forbidden.

#### Import-boundary / no-route / no-DB result

PASS — package scan clean; `NO_ROUTES_DB_MIGRATIONS_OR_FRONTEND`.

#### Platform subject nullable decision

`subject_id: UUID | None` remains nullable until Platform subject resolver is stable. F1 does not depend on `/platform/subjects`.

#### Tests

| Suite | Result |
|---|---|
| `test_passport_contract_boundary.py` | **61 passed** |
| + `test_taxonomy_contract_boundary.py` | **72 passed** |
| `-k "passport or taxonomy or claim"` | **107 passed**, 41 deselected |
| `compileall` + import smoke | **PASSPORT_CONTRACT_IMPORT_OK** |

#### 0052-F1 Decision

**B PASSPORT_CONTRACT_BOUNDARY_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F2**

#### F2 persistence handoff

- Contract models do **not** imply one table per model.  
- F2 must re-inspect existing Profile relational tables.  
- F2 chooses adapter/reuse vs explicit migration with upgrade/downgrade tests.  
- F2 must resolve or safely isolate Platform subjects 500 before hard subject dependency.  
- F2 must not create dual-write Profile/Passport drift.  
- No frontend in F2.

#### Remaining watch items

Profile FE↔BE mismatch; missing Profile tests; Platform subjects 500; shell overflow; PDF 4-family; CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen; nullable subject_id.

**Next slice: 0052-F2 Passport Persistence and Migration**

#### 0052-F2 Guardrails

- May add models + foundation Alembic migration + ownership/compat tests.  
- Must not add frontend, FastAPI Passport routes (unless explicitly re-scoped), or dual-write drift.  
- Must not require non-null Subject until resolver is stable.  
- Must not invent verification or evidence requirements.

### 0052-F2 Passport Persistence and Migration

**Type:** `PERSISTENCE_AND_FOUNDATION_MIGRATION`  
**Status:** Done (this slice)  
**Depends on:** 0052-F1 Decision B  

#### Purpose

Create reversible physical storage for accepted Passport contracts while preserving the existing Profile Data Hub as the single physical source for career-section records. No Passport HTTP APIs, frontend, services, AI, evidence, sharing, CV, or Roadmap integration.

#### Persistence strategy (locked)

**Profile-wrapper.** `CareerPassport` references one existing `Profile` (and optionally one `CareerSubject`), owns Passport preferences/metadata and `PassportTarget` rows, and adapts existing Profile section tables in place.

Parallel Passport section tables (`passport_experiences`, `passport_educations`, etc.) were **rejected** to avoid dual truth, sync jobs, and dual-write drift. The same physical section rows serve both the transitional Profile API and future Passport API (single-write doctrine).

#### Tables created

| Table | Role |
|---|---|
| `career_passports` | Aggregate: owner, profile, optional subject, visibility, version, section prefs, profile meta |
| `passport_targets` | Passport-owned targets (ordering + native record meta) |

#### Existing tables extended

| Table | New fields |
|---|---|
| `work_experiences` | `passport_role_taxonomy`, `passport_record_meta` |
| `educations` | `passport_record_meta` |
| `projects` | `passport_skill_taxonomy`, `passport_record_meta` |
| `skills` | `passport_taxonomy`, `passport_record_meta` |
| `certifications` | `passport_credential_type`, `passport_record_meta` |

#### Aggregate ↔ Profile mapping

| Logical field | Physical source |
|---|---|
| `display_name` | `User.full_name` |
| `headline` | `Profile.professional_headline` |
| `summary` | `Profile.bio_summary` |
| Experience / education / projects / skills / credentials | Existing Profile child tables |

Do not duplicate top-level Profile fields on `career_passports`.

#### Subject handling

`career_passports.subject_id` is **nullable**, FK `career_subjects.id` **ON DELETE SET NULL**. Migration does not require, backfill, or call Platform subject APIs. A Passport is persistable with `subject_id = NULL`.

#### Ownership and delete behavior

| FK | On delete |
|---|---|
| `owner_user_id` → `users.id` | CASCADE (unique) |
| `profile_id` → `profiles.id` | CASCADE (unique) |
| `subject_id` → `career_subjects.id` | SET NULL |
| `passport_targets.passport_id` → `career_passports.id` | CASCADE |

Deleting a Passport cascades to targets and does **not** delete the Profile. One owner / one Profile maps to at most one Passport.

#### Record metadata / backfill

Profile-backed (migrated + inherited) default:

```json
{"source_status":"user_asserted","support_status":"profile_supported","verification_status":"unverified"}
```

Native target default uses `support_status: not_provided`. Never verified / evidence-backed. Projects taxonomy → `[]`. Certifications type → `certification`.

#### Taxonomy storage

Role/skill taxonomy references stored as **JSONB** on section/target rows (object or array as specified). No foreign keys to in-memory taxonomy IDs. No registry lookups in F2.

#### Migration

| Field | Value |
|---|---|
| Revision | `f0008_passport_persistence` |
| Parent | `f0007_privacy_foundation` |
| Foundation head | `f0008_passport_persistence` (single head) |

Upgrade: create tables/indexes/checks → add columns → backfill → NOT NULL + server defaults → named constraints. Creates **zero** automatic Passport/target rows. Leaves legacy Profile content unchanged.

Downgrade to F7: drops Passport tables/columns/checks only; preserves users, profiles, and all original Profile field values. Passport aggregate/target/meta data may be lost (documented).

#### Journey results (disposable PostgreSQL)

| Step | Result |
|---|---|
| Empty upgrade | PASS → head F8; tables/columns/constraints present; 0 Passport rows |
| Legacy-data upgrade | PASS → original IDs/values preserved; meta/taxonomy/type backfilled |
| Persistence | PASS → null subject; defaults; unique owner/profile; target cascade; Profile preserved |
| Downgrade | PASS → Passport gone; Profile intact; revision F7 |
| Re-upgrade | PASS → schema + backfill restored; revision F8 |
| ORM/database drift | `compare_metadata(...) == []` |

#### Profile compatibility

Existing Profile request schemas do not require Passport fields. Section ORM defaults supply Passport meta. `ProfileRead` still serializes legacy fields. No Profile endpoint or request schema changed.

#### Tests

| Suite | Result |
|---|---|
| `test_passport_contract_boundary.py` | **61 passed** |
| `test_migration_policy.py` | PASS (head F8; lineage F8→F7→…→F1) |
| `test_passport_persistence.py` | PASS (real disposable PG journey; no skips) |
| `test_migration_runner.py` | PASS |
| `-k "passport or profile or migration"` (db+unit) | **88 passed** |
| compile + import + foundation-head smoke | **PASSPORT_PERSISTENCE_IMPORT_OK** / **PASSPORT_FOUNDATION_HEAD_OK** |

#### Scope

No frontend, Passport API routes, services, schemas, LLM, dual-write, or Subject API dependency. `NO_FRONTEND_API_SCHEMA_OR_SERVICE_CHANGES`.

#### 0052-F2 Decision

**B PASSPORT_PERSISTENCE_MIGRATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F3**

#### F3 handoff — Passport API MVP

- Create authenticated Passport API schemas and routes.  
- Lazy-create Passport from the current user’s Profile.  
- No owner ID accepted from clients.  
- `subject_id` remains optional.  
- Section operations use existing Profile-backed rows.  
- Targets use `passport_targets`.  
- All ownership checked server-side.  
- No evidence requirement; no verified status; no public sharing.  
- No frontend in F3.  
- No dual write.

#### Remaining watch items

Profile FE↔BE mismatch; incomplete legacy Profile test coverage; Platform subjects local 500 (subject_id stays nullable); shell overflow @390/@768; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen.

**Next slice: 0052-F3 Passport API MVP**

---

### 0052-F3 Passport API MVP

**Type:** `AUTHENTICATED_API_MVP`  
**Status:** Done (this slice)  
**Depends on:** 0052-F2 Decision B  

#### Purpose

Expose a bounded authenticated Passport API over F1 contracts and F2 Profile-wrapper persistence: lazy-create one Passport, wrap the existing Profile, mutate Profile-backed rows and Passport targets, enforce ownership and optimistic concurrency. No frontend, migration, public sharing, evidence, claims, LLM, CV, or Roadmap integration.

#### Route-surface decision

One aggregate read + explicit section-write endpoints (27 authenticated path operations). Aggregate POST omitted because GET lazy-creates. Separate item/list GET endpoints omitted — the complete aggregate read supplies all current Passport data.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/passport` | Lazy-create and read full aggregate |
| PATCH | `/api/v1/passport` | Subject link / section preferences |
| PATCH | `/api/v1/passport/profile` | Profile-backed personal information |
| POST/PUT/PATCH/DELETE | `/api/v1/passport/{collection}…` | experiences, education, projects, skills, credentials, targets |

#### Lazy-create behavior

GET ensures Profile (legacy users) then one Passport wrapping that Profile. No Subject, no targets, no section copies. Idempotent; unique constraints are the race guard. Version starts at 1; GET does not increment version.

#### Profile-wrapper write behavior

Mutations write directly to existing Profile child tables / `passport_targets`. No Profile HTTP calls, no dual-write, no Passport section tables.

#### Response model and output filtering

All successes return `{ "data": PassportRead }`. Derived: `display_name`←User.full_name, `headline`←professional_headline, `summary`←bio_summary. Never exposes `owner_user_id`, `profile_id`, auth secrets, or email.

#### Authentication / ownership

Every operation requires `get_current_user`. Ownership derived server-side. Missing or cross-user entries → **404** (non-disclosing). No client `passport_id` / `owner_user_id` / `profile_id`.

#### Subject linking

Optional. Non-null `subject_id` validated via `ensure_owned_subject` (direct DB). Explicit null clears. No auto-create; no Platform HTTP call.

#### Version / concurrency

Every mutation requires `expected_version` (body or DELETE query). Passport row locked `FOR UPDATE`; mismatch → **409 CONFLICT** with `{expected_version, current_version}`. Success increments version by exactly one. Failed 404/409/422 leave data and version unchanged.

#### Record metadata / taxonomy

Clients cannot submit record metadata. Profile-backed creates use `user_asserted` / `profile_supported` / `unverified`. Targets use `not_provided` / `unverified`. Taxonomy refs advisory JSONB only — freeform text retained; no registry FK; no verification implication.

#### Profile compatibility

Passport profile/section writes are visible via existing `/api/v1/profile`. Profile writes remain visible on Passport GET. Single Profile row; no duplicates.

#### Journey results (disposable PostgreSQL)

Real guarded disposable DB (`ck_0052f3_`), TestClient, foundation head F8, two users. Coverage: 27 routes, auth 401, lazy-create, output filtering, legacy Profile rows, shared-row CRUD all six collections, subject link/cross-user 404, version conflicts, exact-set reorder, mass-assignment 422, no claims/provenance/goals/LLM. **Zero skips.**

#### Tests

| Suite | Result |
|---|---|
| `test_passport_api.py` | **2 passed** (real disposable PG; 0 skips) |
| `test_passport_contract_boundary.py` | **61 passed** |
| `test_passport_persistence.py` | PASS |
| `test_migration_policy.py` | PASS (head F8) |
| Focused passport+persistence+API | **79 passed** |
| compile + route/foundation smoke | **PASSPORT_API_ROUTE_SMOKE_OK** / **PASSPORT_API_FOUNDATION_UNCHANGED_OK** |

#### Scope

`NO_FRONTEND_MODEL_OR_MIGRATION_CHANGES`. No LLM/provider. Foundation remains `f0008_passport_persistence`.

#### 0052-F3 Decision

**B PASSPORT_API_MVP_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F4**

#### F4 handoff — Passport Frontend Shell + Design Fidelity

- Add frontend Passport API types and client methods.  
- Add `/passport` frontend shell only.  
- Use aggregate GET for overview.  
- No complete section editors in F4.  
- Show loading, empty, error, and retry states.  
- Display private/unverified copy honestly.  
- Do not expose raw metadata as debug panels.  
- Design Fidelity required at 1280/768/390.  
- Carry shell-overflow watch.  
- No CV/Roadmap integration until F7.

#### Remaining watch items

Platform subjects list may still fail while direct optional linkage works; Profile FE↔BE mismatch; incomplete legacy Profile coverage; shell overflow @390/@768; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen.

**Next slice: 0052-F4 Passport Frontend Shell + Design Fidelity**

---

### 0052-F3R1 Migration-Head Regression Alignment

**Type:** `BOUNDED_TEST_MAINTENANCE`  
**Status:** Done (this slice)  
**Depends on:** 0052-F3 Decision B  

#### Why

After F3, the wider `-k "passport or profile or platform or migration"` run showed **3 failures**. Root cause: stale historical test assumptions, not a Passport API defect.

| Failure | Stale assumption | Reality |
|---|---|---|
| `test_f0007_migration_empty_to_head` | `foundation_heads() == [F7]` after `prepare_database()` | Current head is F8 |
| `test_f0007_downgrade_upgrade` | `upgrade("head")` leaves revision F7 | `head` means F8 |
| `test_no_f0008_or_observability_migration` | Any `f0008*` migration is forbidden | F8 is Passport persistence |

**F3 implementation accepted.** F3R1 repaired repository test assumptions introduced by later foundation-head advancement. No production, migration, model, API, frontend, or LLM file changed.

#### Repair strategy

- Historical F7: upgrade explicitly to `f0007_privacy_foundation` (not `prepare_database` / `"head"`).  
- Downgrade: F8 → F6 → F7 → `"head"` (F8), asserting privacy tables at F7 and Passport tables at current head.  
- Drift-at-head: assert `foundation_heads() == [CURRENT_HEAD]` where `CURRENT_HEAD = f0008_passport_persistence`.  
- Observability: forbid observability-named migrations only; require F7 and F8 filenames; preserve ORM/table/vendor boundaries.

#### Files changed

| File | Change |
|---|---|
| `backend/app/platform/privacy/tests/test_privacy_service.py` | Historical F7 + F7→head journeys |
| `backend/app/platform/observability/tests/test_observability_boundaries.py` | `test_no_observability_migration` |
| Docs | Master plan + live tracker |

#### Tests

| Suite | Result |
|---|---|
| Privacy + observability targeted | **10 passed**, 0 skips |
| Wider previously-failing run | **339 passed**, 87 deselected, **0 failed** |
| Combined Passport + privacy + observability | **89 passed** |
| Foundation head | unchanged `f0008_passport_persistence` |

#### 0052-F3R1 Decision

**B MIGRATION_HEAD_REGRESSION_ALIGNMENT_ACCEPTED_WITH_NONBLOCKING_WATCHES_F4_UNBLOCKED**

F4 frontend gate unblocked.

#### Remaining watch items

Platform subjects list may 500 while direct subject link works; Profile FE↔BE mismatch; incomplete Profile tests; shell overflow @390/@768; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen.

**Next slice: 0052-F4 Passport Frontend Shell + Design Fidelity**

---

### 0052-F4 Passport Frontend Shell + Design Fidelity

| Field | Value |
|---|---|
| Slice type | `FRONTEND_SHELL_AND_DESIGN_FIDELITY` |
| Status | Completed — Decision B |
| Frontend route | `/passport` (authenticated AppShell) |
| Aggregate client | `passportApi.get()` → `GET /api/v1/passport` only |
| TypeScript contract | `PassportRead` / `PassportEnvelope` + section reads in `types/api.ts` |
| Page structure | Heading, status strip, identity, metrics, seven sections by `section_preferences`, targets preview, privacy card |
| Loading state | Spinner + `aria-busy`; heading remains; no fake data |
| Empty state | Neutral “Passport is ready” copy; Version 1; Private/Unverified |
| Error/retry | `role="alert"` + human message + Retry → `refetch()` |
| Populated state | Counts + section cards + up to three targets; read-only |
| Private/unverified language | Honest labels; no verified/score language |
| Raw metadata | Not exposed; formatter labels only |
| Edits / mutations | None |
| Platform/CV/Roadmap calls | None from Passport page |
| Shared-shell correction | `--current-sidebar-width` drives header + main; menuBtn display fix |
| Desktop (>1024) | Expanded/collapsed sidebar syncs header/main; menu hidden |
| Tablet (768–1024) | 64px icon rail; labels/headings/collapse hidden; menu hidden |
| Mobile (<768) | Off-canvas drawer `min(84vw, 280px)`; menu + backdrop + Escape + nav close |
| Accessibility | h1/h2; aria-expanded/controls; alert; decorative icons hidden |
| Reduced motion | Shell + Passport CSS respect `prefers-reduced-motion` |
| Dark / light | Both verified at 1280 |
| 1280 | Pass — no overflow; sidebar 240px; header left 240px |
| 768 | Pass — icon rail 64px; no overflow |
| 390 | Pass — drawer closed/open; no overflow |
| Overflow measurements | 1280/768/390: `scrollWidth == clientWidth` |
| Frontend tests | PassportPage 5 + AppShellResponsive 3; full suite 97 passed |
| Frontend build | `tsc` + `vite build` PASS |
| Backend contract regression | 63 passed; disposable PG skips = 0; no backend file changes |
| Browser console | No uncaught exceptions; intentional `ERR_FAILED` only during abort test |
| Screenshots | `~/Desktop/CareerKundi_0052_F4_Design_Fidelity/` |
| Exact files | 15 allowed paths (types, api, App, layout×6+test, passport×3, 2 docs) |
| Verdict | **B PASSPORT_FRONTEND_SHELL_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F5** |

#### F5 handoff

- Implement Profile, Experience and Education editors only
- Use existing Passport PATCH/POST/PUT/DELETE APIs
- Every mutation sends current `expected_version`
- Handle 409 by refetching and warning
- Update TanStack Query aggregate cache after success
- No Projects/Skills/Credentials/Targets editors until F6
- No Subject picker unless Platform resolver/list is stable
- No CV/Roadmap integration until F7
- Preserve private/unverified language; no completion-pressure scoring

#### Remaining watch items

Platform subjects list may 500 while direct subject link works; Profile FE↔BE mismatch; incomplete Profile tests; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen; frontend ESLint config missing at baseline (focused lint blocked).

Shell-overflow watch **cleared** (1280/768/390 overflow OK).

**Next slice: 0052-F5 Passport Profile, Experience and Education Editing**

---

### 0052-F5 Passport Profile, Experience and Education Editing

| Field | Value |
|---|---|
| Slice type | `FRONTEND_EDITING_MVP` |
| Status | Completed — Decision B |
| Frontend route | `/passport` (unchanged) |
| Mutation client surface | `passportApi.patchProfile`, experience create/patch/delete/reorder, education create/patch/delete/reorder |
| Profile editor fields | phone, nationality, linkedin_url, github_url, portfolio_url, address_city, address_country, professional_headline, bio_summary, interests |
| Experience editor | add / edit / delete (confirm) / up-down reorder; no taxonomy editing |
| Education editor | add / edit / delete (confirm) / up-down reorder |
| expected_version | Sent on every mutation; read from aggregate at submit time |
| 409 conflict | Warning + refetch aggregate; no silent overwrite |
| Cache update | `queryClient.setQueryData(["passport", "aggregate"], next)` from mutation response |
| Validation | Required fields; date order; `is_current` clears end_date; client blocks before request |
| Delete confirmation | Explicit confirm before DELETE |
| Optional reorder | Up/Down buttons; full `ordered_ids` + expected_version |
| Forbidden sections | Projects / Skills / Credentials / Targets remain read-only |
| Subject picker | None |
| CV / Roadmap integration | None from Passport feature |
| Verification / evidence / public sharing | None |
| Private / unverified copy | Preserved |
| Tests | Form utils 6; Edit forms 9; Passport page 10; full frontend suite PASS |
| Browser conflict journey | Two-tab stale version → 409 + warning + refetch |
| Browser validation journey | Blank title/company/degree/institution + date order blocked |
| Design Fidelity viewports | 1280 / 768 / 390 — no horizontal overflow |
| Screenshots | `~/Desktop/CareerKundi_0052_F5_Design_Fidelity/` |
| Exact files | 12 allowed paths (types, api, passport×8, 2 docs) |
| Verdict | **B PASSPORT_PROFILE_EXPERIENCE_EDUCATION_EDITING_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F6** |

#### F6 handoff

- Add Projects, Skills, Credentials and Career Targets editors
- Use existing Passport section mutation APIs
- Keep `expected_version` on every mutation
- Keep 409 refetch + conflict warning behavior
- Continue TanStack Query cache update from returned aggregate
- No Subject picker unless Platform list behavior is stable
- No CV/Roadmap integration until F7
- Keep private/unverified language
- No completion-pressure scoring

#### Remaining watch items

Platform subjects list may 500 while direct subject link works; Profile FE↔BE mismatch; incomplete Profile tests; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen; frontend ESLint config missing at baseline (focused lint blocked). Incidental shell `GET /api/v1/roadmap/` may occur outside Passport feature (not a Passport client).

**Next slice: 0052-F6 Passport Projects, Skills, Credentials and Targets Editing**

---

### 0052-F6 Passport Projects, Skills, Credentials and Targets Editing

| Field | Value |
|---|---|
| Slice type | `FRONTEND_REMAINING_SECTION_EDITORS` |
| Status | Completed — Decision B |
| Frontend route | `/passport` (unchanged) |
| Mutation client surface | Projects / Skills / Credentials / Targets create, patch, delete, reorder |
| Project editor | add / edit / delete (confirm) / Up-Down reorder; no taxonomy API |
| Skill editor | add / edit / delete (confirm) / Up-Down reorder; type/proficiency selects; no taxonomy API |
| Credential editor | thin references only; truth copy “Credential reference · Not independently verified” |
| Target editor | career intentions only; truth copy “Career target · Not a Roadmap yet”; optional advisory role taxonomy text |
| expected_version | Sent on every mutation |
| 409 conflict | Warning + refetch aggregate; no silent overwrite |
| Cache update | `setQueryData(["passport","aggregate"], next)` from mutation response |
| Validation | Required fields; date/expiry order; priority clamped 1–5 |
| Delete confirmation | Required before DELETE |
| Reorder | Up/Down; full `ordered_ids` + expected_version |
| Subject picker | None |
| CV / Roadmap integration | None from Passport feature |
| Taxonomy lookup | None |
| Verification / evidence / public sharing | None |
| Private / unverified copy | Preserved |
| F5 editors | Profile / Experience / Education preserved |
| Tests | Form utils 7; Edit forms 18; Passport page 11; full frontend 128 passed |
| Browser conflict journey | Stale target create → 409 + warning + refetch |
| Browser validation journey | Blank project/skill/credential/target fields + date/expiry order |
| Design Fidelity viewports | 1280 / 768 / 390 — no horizontal overflow |
| Screenshots | `~/Desktop/CareerKundi_0052_F6_Design_Fidelity/` |
| Exact files | 12 allowed paths |
| Verdict | **B PASSPORT_REMAINING_SECTION_EDITORS_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F7** |

#### F7 handoff

- Profile compatibility review
- CV Builder may read Passport aggregate but must not mutate Passport without explicit versioned actions
- Roadmap may prefill from Passport targets but remains Roadmap-owned
- Subject picker remains blocked unless Platform list behavior is stable
- no public sharing
- no verification claims
- no completion-pressure scoring
- keep 409 conflict strategy for any Passport mutation
- maintain query cache from returned aggregate

#### Remaining watch items

Platform subjects list may 500 while direct subject link works; Profile FE↔BE mismatch; incomplete Profile tests; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen; frontend ESLint config missing at baseline; incidental shell roadmap fetch outside Passport feature; dual local/Docker `:8000` listeners can break auth during browser checks (stop Docker backend when using local uvicorn).

**Next slice: 0052-F7 Profile Compatibility + CV/Roadmap Integration**

---

### 0052-F7 Profile Compatibility + CV/Roadmap Integration

| Field | Value |
|---|---|
| Slice type | `COMPATIBILITY_AND_READ_INTEGRATION` |
| Status | Completed — Decision B |
| Backend production changes | None |
| Database / migrations | None |
| Profile compatibility | Legacy `/profile` no longer claims AI source-of-truth; Passport primary structured editor copy + CTA |
| Old source-of-truth wording | Removed (`single source of truth for all AI features` absent) |
| Profile Passport CTA | `Open Career Passport` → `/passport` |
| Profile Passport read | Non-blocking `passportApi.get()`; failure does not break Profile |
| CV Passport card | Read-only readiness card; Private and unverified; Edit in Career Passport |
| CV section selection | `Use Passport sections for this CV` maps enabled usable Passport sections → CV section IDs |
| CV target role prefill | One-click from Passport targets into CV role text |
| CV ownership boundary | Still `cvApi.generate` / `update`; no `passport_id`; no Passport mutations |
| Roadmap target prefill | Generate modal “Use a Career Passport target”; prefills role + context |
| Roadmap ownership boundary | Roadmap-owned `personalization_inputs.passport_target_prefill` (human fields only); no Passport ID |
| Passport mutations outside `/passport` | None from Profile / CV / Roadmap |
| Subject picker | None |
| Platform Subject calls | None from F7 surfaces |
| Public sharing | None |
| Verification / evidence claims | None |
| Private / unverified copy | Required patterns present |
| Tests | Integration utils 5; Profile 2; CV 3; Roadmap 2; Passport regression 36; full frontend 140 passed |
| Browser Profile journey | PASS — compatibility card, CTA, no mutation |
| Browser CV journey | PASS — sections + target prefill; POST `/cv-builder/generate`; no passport_id |
| Browser Roadmap journey | PASS — prefill + boundary copy; POST `/roadmap/generate`; no Platform subjects |
| Design Fidelity viewports | 1280 / 768 / 390 — no horizontal overflow |
| Screenshots | `~/Desktop/CareerKundi_0052_F7_Profile_CV_Roadmap_Integration/` |
| Exact files | 12 allowed paths |
| Verdict | **B PASSPORT_PROFILE_CV_ROADMAP_INTEGRATION_ACCEPTED_WITH_WATCH_ITEMS_READY_FOR_0052_F8** |

#### F8 handoff

- Final Passport hardening, observability, and full regression
- Audit all Passport-related pages for forbidden language
- Verify no unintended Passport mutations outside `/passport`
- Verify Profile / CV / Roadmap integration boundaries remain read-only for Passport
- Fix or formally defer Platform subjects list 500
- Fix or formally defer frontend ESLint config
- Address incidental shell Roadmap fetch if still present
- No public sharing unless a new phase is approved
- No verification / evidence claims unless 0053 starts

#### Remaining watch items

Platform subjects list may 500 while direct subject link works; Profile FE↔BE mismatch; incomplete Profile tests; PDF 4-family; Platform CORS; RoleTaxonomyAgent ≠ 0051 API; 004E/Auto Apply frozen; frontend ESLint config missing at baseline; incidental shell roadmap fetch outside Passport feature; dual local/Docker `:8000` listeners can break auth during browser checks (stop Docker backend when using local uvicorn).

**Next slice: 0052-F8 Passport Hardening, Observability and Final Regression**

---

### 0052-F8 Passport Hardening, Observability and Final Regression

| Field | Value |
|---|---|
| Slice type | `FINAL_HARDENING_OBSERVABILITY_REGRESSION` |
| Status | Completed — Decision B |
| Track | **B** — bounded Profile FE↔BE skills/certs render repair + Track A audit/tests/docs |
| Boundary audit | Static `passportBoundaryAudit.test.ts` PASS |
| Mutation boundary | Profile/CV/Roadmap/Dashboard: `passportApi.get` only (Dashboard uses none) |
| Forbidden language | Absent on audited user-facing pages |
| Privacy / unverified | Private + Unverified retained; no public sharing |
| Profile compatibility | Card + CTA; object-skill crash fixed (normalize skill/cert labels) |
| CV Builder boundary | Read-only Passport awareness; no `passport_id`; no Passport mutations |
| Roadmap boundary | Target prefill only; no Platform subjects; no Passport mutations |
| Dashboard watch | Incidental `roadmapApi.list` remains; soft-fail to “No roadmap yet”; non-blocking (documented + tested) |
| Platform subjects watch | **Cleared** — authenticated empty list `200 {data:[], meta:{count:0}}` in F8 browser + existing API tests |
| Observability | No new observability storage/migrations; boundary tests PASS |
| Frontend tests | Boundary 6; Dashboard 2; Profile 3; targeted 57; full 149 passed |
| Backend tests | Targeted 92; wider path+keyword 339 passed; disposable PG skips 0 |
| Browser | Passport/Profile/CV/Roadmap/Dashboard PASS; conflict 409; expected_version on UI skill create |
| Design Fidelity | 1280 / 768 / 390 — no horizontal overflow |
| Screenshots | `~/Desktop/CareerKundi_0052_F8_Final_Hardening/` |
| Exact files | Track B: ProfilePage + tests/docs/audit/Dashboard test |
| Verdict | **B PASSPORT_FINAL_HARDENING_ACCEPTED_WITH_DEFERRED_WATCHES_0052_COMPLETE** |

#### Final 0052 status

**0052 Career & Education Passport is completed and accepted.**

No public sharing, verification, evidence claims, or completion-pressure scoring are included in 0052.

#### Remaining deferred watches

- Incomplete Profile tests beyond F8 object-skill coverage (broader FE↔BE shapes)
- PDF 4-family
- Platform CORS
- RoleTaxonomyAgent ≠ 0051 API
- 004E / Auto Apply frozen
- Frontend ESLint config missing (`FOCUSED_LINT: FORMALLY_DEFERRED_BASELINE_NO_ESLINT_CONFIG`)
- Incidental Dashboard Roadmap fetch (documented non-blocking; not removed)
- Dual local/Docker `:8000` runtime hygiene (documented; stop Docker backend for local uvicorn)

#### Next phase recommendation

**0053 Evidence, Claims, Provenance and Verification Foundations** — start with **0053-F0** (planning only). Carry deferred Passport watches above into later hardening as needed.

**0052 closed. No 0052-F9.**

---

## LLM-R1 Local Ollama 8B Provider Alignment

**Status:** Completed in this commit (gate before 0053-F1).

| Field | Value |
|---|---|
| Active provider | Local Ollama 8B |
| Default API | `http://127.0.0.1:11434` |
| Default models | `OLLAMA_MODEL_FLASH` / `OLLAMA_MODEL_PRO` (default `llama3.1:8b`) |
| Mock / tests | `LLM_PROVIDER=mock` → deterministic mock |
| Gemini | Deprecated legacy config only — **not** the active provider |
| Embeddings | Local hash embeddings for now; **LLM-R2** deferred for local embedding migration |

Owner decision: CareerKundi no longer uses Gemini API as the current/default LLM provider.

Local LLM output is not verification and is not guaranteed correct.

**Next product gate after LLM-R1 acceptance:** CORE-VALUE-R1 → JOB-INT-R1 → ROADMAP-RICH-CONTENT → POST-CLAUDE-R2 audit → then **0053-F1 Claim Service Contract Boundary**.

## CORE-VALUE-R1 CV Automation and Roadmap Learning Content

**Status:** Done (`cc7610b3`). Quick CV + study/practice normalize.

## JOB-INT-R1 Interview Answer Realism

**Status:** Done (`8ac8793a`). Central interview-pack prompt via `build_interview_pack_system_prompt()` in `InterviewPackExecutorAgent`; candidate-answer contract + claim integrity tests; still `get_llm()` / local Ollama only.

## ROADMAP-RICH-CONTENT Bloom-Aligned Learning Path

**Status:** Done (`893a4812`). `learning_content.py` enrichment; schema flashcards/quizzes/projects/reflection; RoadmapPage renders enriched practice tabs.

## POST-CLAUDE-R2 Integration Audit

**Status:** Done (`3d7cc7d1`). Evidence: `~/Desktop/CareerKundi_POST_CLAUDE_R2_Integration_Audit_Evidence.txt`.

## 0053-F1 Claim Service Contract Boundary

**Status:** Done (`9e221bac`). Create-time allowlists, source/snapshot rules, safe display labels; **no** evidence records, verification reviews, or public claim routes.

Evidence: `~/Desktop/CareerKundi_0053_F1_Claim_Service_Contract_Boundary_Evidence.txt`.

## 0053-F2 Evidence Domain Skeleton

**Status:** Done (`112fc8e8`). Private `EvidenceRecord` + `ClaimEvidenceLink` + `f0009_evidence_foundation`; service helpers; **no** upload/download, verification workflow, public routes, or frontend.

Evidence: `~/Desktop/CareerKundi_0053_F2_Evidence_Domain_Skeleton_Evidence.txt`.

## 0053-F3 Private Evidence Service/API Boundary

**Status:** Done (`dd3c4bdb`). Authenticated `/api/v1/evidence` metadata + claim-link APIs; current-user scoping; **no** upload/download, frontend, Passport panel, or verification workflow.

Evidence: `~/Desktop/CareerKundi_0053_F3_Private_Evidence_API_Boundary_Evidence.txt`.

## 0053-F4 Private Evidence Library UI + Attachment Storage Decision

**Status:** Done (`cd0194fe`). Private `/evidence` metadata UI + client; storage decision documented for F5; **no** upload/download/storage backend, Passport evidence panel, or claim linker.

Evidence: `~/Desktop/CareerKundi_0053_F4_Private_Evidence_Library_UI_Evidence.txt`.

## 0053-F5 Attachment Storage Backend

**Status:** Done (`c298d33c`). Local private `LocalEvidenceStorage` + owner-only `POST/GET /api/v1/evidence/{id}/attachment`; updates `storage_uri` / hash / mime / size; **no** frontend upload UI in F5, public URLs, OCR, verification, or Passport/CV/Roadmap/Jobs integrations.

Evidence: `~/Desktop/CareerKundi_0053_F5_Attachment_Storage_Backend_Evidence.txt`.

## 0053-F6 Evidence Upload UI

**Status:** Done (`671b6878`). Evidence Library private attach/download UI against F5 APIs; client size/MIME guards; authenticated blob download; **no** public URL, verification, OCR, Passport/CV/Roadmap/Jobs integrations, or backend storage changes.

Evidence: `~/Desktop/CareerKundi_0053_F6_Evidence_Upload_UI_Evidence.txt`.

## 0053-F7 Evidence-to-Claim Linking UI

**Status:** Done (`ff084051`). Evidence-scoped `GET /linkable-claims` + Evidence Library claim selector/link UI; link does **not** mutate claim axes or verify claims; **no** Passport evidence panel, claim creation UI, public sharing, or `/api/v1/claims`.

Evidence: `~/Desktop/CareerKundi_0053_F7_Evidence_To_Claim_Linking_UI_Evidence.txt`.

## 0053-F8 Passport Read-Only Evidence Panel

**Status:** Done (`6ab2044b`). Evidence-scoped `GET /private-awareness-summary` + Passport `Private evidence awareness` panel; Passport does **not** own evidence, upload/download/link/verify, or mutate claim axes; **no** public sharing, OCR, or verification workflow.

Evidence: `~/Desktop/CareerKundi_0053_F8_Passport_Read_Only_Evidence_Panel_Evidence.txt`.

## 0053-F9 Review/Verification State Machine Planning

**Status:** Done (`1b4fd102`). Pure domain `ReviewState` contracts under `backend/app/platform/verification/`; transition validator + safe labels; **no** verification UI or claim mutation. Upload/link/source ≠ verification.

Evidence: `~/Desktop/CareerKundi_0053_F9_Verification_State_Machine_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f9_verification_state_machine.md`.

## 0053-F10 Review Request Backend Skeleton

**Status:** Done (`e274f9dc`). `review_requests` + `f0010_review_request_foundation` + `/api/v1/review-requests` request/list/get/cancel; **no** approve/reject, claim mutation, verification UI, or public sharing. Review request ≠ verification.

Evidence: `~/Desktop/CareerKundi_0053_F10_Review_Request_Backend_Skeleton_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f10_review_request_backend.md`.

## 0053-F11 Review Request UI

**Status:** Done (`40e96873`). Passport evidence panel private request/cancel UI via F10 APIs; **no** approve/reject, claim mutation, verification badge, public sharing, Passport upload/download, or CV/Roadmap/Jobs review UI. Review request ≠ verification.

Evidence: `~/Desktop/CareerKundi_0053_F11_Review_Request_UI_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f11_review_request_ui.md`.

## 0053-F12 Review Intake Hardening

**Status:** Done (`e1b86413`). Create requires owned claim + linked private evidence; note/reason trim and length bounds; Passport intake copy/errors; **no** approve/reject, claim mutation, malware scan, OCR, or verification outcome. Review request ≠ verification.

Evidence: `~/Desktop/CareerKundi_0053_F12_Review_Intake_Hardening_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f12_review_intake_hardening.md`.

## 0053-F13 Evidence Attachment Safety / Malware Scan Planning

**Status:** Completed / accepted. Pure attachment safety states + derived API/FE warnings; default `scan_not_available`; **no** scan engine, parsing/OCR, LLM review, DB migration, or verification outcome.

Evidence: `~/Desktop/CareerKundi_0053_F13_Attachment_Safety_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f13_attachment_safety_planning.md`.

## 0053-F14 Private Attachment Deletion + Retention Policy

**Status:** Completed / accepted. Owner-only private attachment byte deletion + metadata clear; EvidenceRecord / claim links / review requests / claim statuses retained; **no** scanner, parsing/OCR, LLM review, EvidenceRecord deletion, or verification mutation.

Evidence: `~/Desktop/CareerKundi_0053_F14_Attachment_Deletion_Retention_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f14_attachment_deletion_retention.md`.

## 0053-F15 Runtime Badge-Seed Startup Reliability Fix

**Status:** Completed / accepted. Skip-safe badge catalogue seed + lifespan timeout bound so local uvicorn/OpenAPI readiness is not blocked; **no** product feature, evidence/review/Passport, claim, scan, or LLM provider changes.

Evidence: `~/Desktop/CareerKundi_0053_F15_Runtime_Badge_Seed_Fix_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f15_runtime_badge_seed_fix.md`.

## 0053-F16 Attachment Scan Queue Skeleton

**Status:** Completed / accepted. Internal `attachment_scan_jobs` queue + service helpers; **no** scanner engine, scan route/UI, OCR/parsing, LLM review, claim mutation, or public sharing. Public attachment safety remains `scan_not_available`.

Evidence: `~/Desktop/CareerKundi_0053_F16_Attachment_Scan_Queue_Skeleton_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f16_scan_queue_skeleton.md`.

## 0053-F17 Scan Worker Contract + Quarantine Policy

**Status:** Completed / accepted. Pure worker contract + quarantine policy helpers; scanner availability unavailable; update plans not applied; quarantine not active; **no** engine, route/UI, file I/O, OCR/LLM, claim mutation, or DB migration.

Evidence: `~/Desktop/CareerKundi_0053_F17_Scan_Worker_Quarantine_Policy_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f17_scan_worker_quarantine_policy.md`.

## 0053-F18 Scanner Adapter Interface + No-Op Adapter

**Status:** Completed / accepted. Protocol + `NoopUnavailableScannerAdapter` + factory returning no-op only; verdict `not_run`; **no** real engine, ClamAV/VirusTotal, file I/O, OCR/LLM, scan route/UI, claim mutation, or DB apply.

Evidence: `~/Desktop/CareerKundi_0053_F18_Scanner_Adapter_Noop_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f18_scanner_adapter_noop.md`.

## 0053-F19 Local Scanner Integration Planning

**Status:** Completed / accepted. Planning/policy only (`attachment_scanner_policy.py`); `REAL_SCANNER_ENABLED=False`; future family `local_process_scanner`; **no** engine, packages, route/UI, OCR/LLM, claim mutation, or DB apply.

Evidence: `~/Desktop/CareerKundi_0053_F19_Local_Scanner_Integration_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f19_local_scanner_integration_planning.md`.

## 0053-F20 Disabled Local Scanner Adapter Skeleton

**Status:** Completed / accepted. `DisabledLocalProcessScannerAdapter` scaffold only; factory still returns no-op; **no** subprocess, packages, file I/O, OCR/LLM, scan route/UI, claim mutation, or DB apply.

Evidence: `~/Desktop/CareerKundi_0053_F20_Disabled_Local_Scanner_Adapter_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f20_disabled_local_scanner_adapter.md`.

## 0053-F21 Local Scanner Runtime Safety Contract

**Status:** Completed / accepted. Runtime safety policy only (`attachment_scanner_runtime_policy.py`); `LOCAL_SCANNER_RUNTIME_ENABLED=False`; no shell/network; empty binaries; safe output normalization; **no** command execution, packages, file I/O, OCR/LLM, scan route/UI, claim mutation, or DB apply.

Evidence: `~/Desktop/CareerKundi_0053_F21_Local_Scanner_Runtime_Safety_Contract_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f21_local_scanner_runtime_safety_contract.md`.

## 0053-F22 Scanner Result Persistence Guard

**Status:** Completed / accepted. Internal `AttachmentScanJob` persistence guard only; explicit `apply_to_database=True` plans; transition validation; F21 normalization; **no** scanner execution, packages, file I/O, OCR/LLM, scan route/UI, Evidence/Claim/Review mutation, or quarantine storage.

Evidence: `~/Desktop/CareerKundi_0053_F22_Scanner_Result_Persistence_Guard_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f22_scanner_result_persistence_guard.md`.

## 0053-F23 Quarantine Storage Planning + Disabled Store Contract

**Status:** Completed / accepted. Disabled quarantine storage contract only (`attachment_quarantine_storage.py`); all storage flags `False`; decision objects only; **no** directory, file move/copy/delete, scanner execution, packages, routes/UI, Evidence/Claim/Review mutation, or allowing `quarantined` persistence.

Evidence: `~/Desktop/CareerKundi_0053_F23_Quarantine_Storage_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f23_quarantine_storage_planning.md`.

## 0053-F24 Quarantine Event/Audit Planning + Disabled Audit Sink Contract

**Status:** Completed / accepted. Disabled quarantine audit sink only (`attachment_quarantine_audit.py`); metadata-only event types; F21 redaction; **no** DB/file persistence, routes/UI, scanner/quarantine enforcement, or auto-emission from persistence.

Evidence: `~/Desktop/CareerKundi_0053_F24_Quarantine_Audit_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f24_quarantine_audit_planning.md`.

## 0053-F25 Scan/Quarantine Admin Boundary Planning

**Status:** Completed / accepted. Disabled admin surface contract only (`attachment_scan_admin_boundary.py`); surface/API/UI and trust/leak powers all `False`; planned visibility-only actions; **no** admin routes/UI/workflows, scanner/quarantine/audit activation, or trust-state mutation.

Evidence: `~/Desktop/CareerKundi_0053_F25_Scan_Quarantine_Admin_Boundary_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f25_scan_quarantine_admin_boundary.md`.

## 0053-F26 Scanner Worker Dry-Run Planning + Disabled Runner Contract

**Status:** Completing in this commit. Disabled scanner worker dry-run contract only (`attachment_scan_worker_dry_run.py`); all runner flags `False`; decision objects only; **no** worker loop, startup registration, DB mutation, file access, scanner execution, or persistence/adapter calls.

Evidence: `~/Desktop/CareerKundi_0053_F26_Scanner_Worker_Dry_Run_Planning_Evidence.txt`.  
Doc: `docs/product/careerkundi_0053_f26_scanner_worker_dry_run_planning.md`.

**Next after F26 acceptance:** 0053-F27 only (Scanner Worker Reservation Guard).

---

## 0053 Evidence, Claims, Provenance and Verification Foundations

**Phase status:** Active — **0053-F0** planning complete (docs only).  
**Prior phase:** **0052 Career & Education Passport** — completed and accepted (`8af9b813…`).  
**Plan document:** `docs/product/careerkundi_0053_claims_evidence_plan.md`  
**Foundation head (after F2):** `f0009_evidence_foundation`

### Purpose

Add evidence and claim-support foundations carefully, without public sharing or verification claims in early slices. Preserve Passport as private and unverified by default.

### 0053-F0 (this slice)

| Field | Value |
|---|---|
| Slice type | `PLANNING_AND_BOUNDARY_AUDIT_ONLY` |
| Implementation | **Forbidden** — docs only |
| Public sharing | Forbidden |
| Verification claims / UI | Forbidden |
| Evidence upload | Forbidden |
| Wallet / DID / blockchain | Forbidden |
| Migrations / routes / UI / tests | Forbidden |

### Critical truth rule

> A source, snapshot, uploaded file, user assertion, or claim record is **not** verification.

Supported product wording includes: Self-declared, Profile-backed, Source-linked, Evidence-linked, Under review, Not independently verified, Verified by issuer, Verified by CareerKundi (only after real workflow), Rejected, Expired, Needs review.

### Current repository findings (F0)

| Area | Finding |
|---|---|
| Provenance | Owns Source/Snapshot only; Source ≠ Snapshot; no claims/evidence ownership |
| Claims | `ClaimRecord` / `career_claims` via `f0004_claim_foundation.py`; optional source/snapshot FKs are provenance links only; service create/get/list; **no public claim HTTP routes** |
| Status axes | Independent `support_status` and `verification_status`; no silent upgrades |
| Passport | Private; `verification_status` forced unverified; no evidence/claims ownership; no public sharing |
| Evidence objects | **F2 skeleton:** `evidence_records` + `claim_evidence_links` (metadata/link only; no upload) |
| Verification workflow | **Not implemented** |

### W3C VC 2.0 note (planning guidance only)

Verifiability of a credential does not imply the truth of the claims encoded in it. Do not equate has-source / has-snapshot / has-upload / has-claim-row with verified truth. Do not jump to VC issuance, DID, wallet, or cryptographic presentation in early 0053.

### Planned slice ladder

| Slice | Name |
|---|---|
| 0053-F0 | Planning and Boundary Audit *(this slice)* |
| 0053-F1 | Claim Service Contract Boundary |
| 0053-F2 | Evidence Domain Skeleton |
| 0053-F3 | Private Evidence Service/API Boundary |
| 0053-F4 | Private Evidence Library UI + Storage Decision |
| 0053-F5 | Attachment Storage Backend |
| 0053-F6 | Evidence Upload UI |
| 0053-F7 | Evidence-to-Claim Linking UI |
| 0053-F8 | Passport Read-Only Evidence Panel |
| 0053-F9 | Review/Verification State Machine Planning |
| 0053-F10 | Review Request Backend Skeleton |
| 0053-F11 | Review Request UI |
| 0053-F12 | Review Intake Hardening |
| 0053-F13 | Evidence Attachment Safety / Malware Scan Planning |
| 0053-F14 | Private Attachment Deletion + Retention Policy |
| 0053-F15 | Runtime Badge-Seed Startup Reliability Fix |
| 0053-F16 | Attachment Scan Queue Skeleton |
| 0053-F17 | Scan Worker Contract + Quarantine Policy |
| 0053-F18 | Scanner Adapter Interface + No-Op Adapter |
| 0053-F19 | Local Scanner Integration Planning |
| 0053-F20 | Disabled Local Scanner Adapter Skeleton |
| 0053-F21 | Local Scanner Runtime Safety Contract |
| 0053-F22 | Scanner Result Persistence Guard |
| 0053-F23 | Quarantine Storage Planning |
| 0053-F24 | Quarantine Event/Audit Planning |
| 0053-F25 | Scan/Quarantine Admin Boundary Planning |
| 0053-F26 | Scanner Worker Dry-Run Planning |
| 0053-F27 | Scanner Worker Reservation Guard |

### Hard no-go (until specifically approved)

Public Passport sharing; employer/university/license verification portals; credential wallet; DID/blockchain; cryptographic VC issuance; AI-only verification; automatic public trust / Passport strength scores.

### Next gate

**Owner acceptance of 0053-F26**, then **0053-F27** only.

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
