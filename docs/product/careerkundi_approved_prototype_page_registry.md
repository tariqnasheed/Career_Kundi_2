# CareerKundi Approved Prototype Page Registry

Status: **APPROVED_DESIGN_TARGET**

This registry is the stable P01-P46 interface contract. It does not claim that every page, route, backend service, or interaction is currently implemented.

| Page | Page name | Route | Product group | Approved sheets |
|---|---|---|---|---|
| P01 | Homepage | `/` | Public and Authentication | P01-A4-01, P01-A4-02 |
| P02 | Sign Up | `/register` | Public and Authentication | P02-A4-01, P02-A4-02 |
| P03 | Login | `/login` | Public and Authentication | P03-A4-01 |
| P04 | Password Recovery and Email Verification | `/forgot-password | /reset-password | /verify-email` | Public and Authentication | P04-A4-01, P04-A4-02 |
| P05 | Onboarding | `/onboarding` | Public and Authentication | P05-A4-01, P05-A4-02, P05-A4-03 |
| P06 | Dashboard | `/dashboard` | Core Account and Career Identity | P06-A4-01, P06-A4-02, P06-A4-03 |
| P07 | Profile | `/profile` | Core Account and Career Identity | P07-A4-01, P07-A4-02 |
| P08 | Career Passport | `/passport` | Core Account and Career Identity | P08-A4-01, P08-A4-02, P08-A4-03, P08-A4-04 |
| P09 | CV Builder Overview | `/cv-builder` | CV Builder | P09-A4-01, P09-A4-02 |
| P10 | CV Editor, Preview and Export | `/cv-builder/new | /cv-builder/:cvId` | CV Builder | P10-A4-01, P10-A4-02, P10-A4-03, P10-A4-04 |
| P11 | Job Discovery | `/jobs` | Jobs and Applications | P11-A4-01, P11-A4-02, P11-A4-03 |
| P12 | Job Details and Role Intelligence | `/jobs/:jobId` | Jobs and Applications | P12-A4-01, P12-A4-02, P12-A4-03 |
| P13 | Saved Jobs | `/saved-jobs` | Jobs and Applications | P13-A4-01, P13-A4-02 |
| P14 | Applications Tracker | `/applications` | Jobs and Applications | P14-A4-01, P14-A4-02, P14-A4-03 |
| P15 | Application Detail | `/applications/:applicationId` | Jobs and Applications | P15-A4-01, P15-A4-02 |
| P16 | Interview Preparation Overview | `/interview-prep` | Interview Preparation | P16-A4-01, P16-A4-02 |
| P17 | Interview Pack Detail | `/interview-packs/:packId` | Interview Preparation | P17-A4-01, P17-A4-02, P17-A4-03, P17-A4-04, P17-A4-05, P17-A4-06 |
| P18 | Mock Interview Session | `/mock-interview/:sessionId` | Interview Preparation | P18-A4-01, P18-A4-02, P18-A4-03 |
| P19 | Skill Library | `/skills` | Skills and Assessments | P19-A4-01, P19-A4-02 |
| P20 | Skill Detail | `/skills/:skillId` | Skills and Assessments | P20-A4-01, P20-A4-02, P20-A4-03 |
| P21 | Skill Practice Session | `/skills/:skillId/practice` | Skills and Assessments | P21-A4-01, P21-A4-02, P21-A4-03, P21-A4-04 |
| P22 | Assessment Results | `/assessments/:assessmentId/results` | Skills and Assessments | P22-A4-01, P22-A4-02 |
| P23 | Roadmap Generator | `/roadmap/new` | Career Roadmap | P23-A4-01, P23-A4-02, P23-A4-03 |
| P24 | Roadmap Overview | `/roadmap | /roadmap/:roadmapId` | Career Roadmap | P24-A4-01, P24-A4-02, P24-A4-03 |
| P25 | Roadmap Milestone and Learning Detail | `/roadmap/:roadmapId/milestones/:milestoneId` | Career Roadmap | P25-A4-01, P25-A4-02, P25-A4-03, P25-A4-04 |
| P26 | Study-Abroad Dashboard | `/study-abroad` | Study Abroad | P26-A4-01, P26-A4-02, P26-A4-03 |
| P27 | Country Comparison | `/study-abroad/countries` | Study Abroad | P27-A4-01, P27-A4-02 |
| P28 | University and Programme Search | `/study-abroad/programs` | Study Abroad | P28-A4-01, P28-A4-02, P28-A4-03 |
| P29 | University and Programme Detail | `/study-abroad/programs/:programId` | Study Abroad | P29-A4-01, P29-A4-02, P29-A4-03 |
| P30 | Eligibility Assessment | `/study-abroad/eligibility` | Study Abroad | P30-A4-01, P30-A4-02 |
| P31 | Budget Planner | `/study-abroad/budget` | Study Abroad | P31-A4-01, P31-A4-02 |
| P32 | Scholarships | `/study-abroad/scholarships` | Study Abroad | P32-A4-01, P32-A4-02 |
| P33 | Test Preparation | `/study-abroad/test-preparation` | Study Abroad | P33-A4-01, P33-A4-02 |
| P34 | SOP and LOR Preparation | `/study-abroad/sop-lor` | Study Abroad | P34-A4-01, P34-A4-02, P34-A4-03 |
| P35 | Study-Abroad Document Checklist | `/study-abroad/documents` | Study Abroad | P35-A4-01, P35-A4-02 |
| P36 | Study-Abroad Application Tracker | `/study-abroad/applications` | Study Abroad | P36-A4-01, P36-A4-02, P36-A4-03 |
| P37 | Visa Preparation | `/study-abroad/visa` | Study Abroad | P37-A4-01, P37-A4-02 |
| P38 | Platform Foundation | `/platform` | Platform, Evidence and Reviews | P38-A4-01, P38-A4-02 |
| P39 | Evidence Library | `/evidence` | Platform, Evidence and Reviews | P39-A4-01, P39-A4-02, P39-A4-03, P39-A4-04 |
| P40 | Claim Management and Evidence Linking | `/claims` | Platform, Evidence and Reviews | P40-A4-01, P40-A4-02, P40-A4-03 |
| P41 | Private Review Requests | `/review-requests` | Platform, Evidence and Reviews | P41-A4-01, P41-A4-02, P41-A4-03 |
| P42 | Achievements | `/achievements` | Progress and Account Management | P42-A4-01, P42-A4-02 |
| P43 | Notifications and Activity | `/notifications` | Progress and Account Management | P43-A4-01, P43-A4-02 |
| P44 | Settings | `/settings` | Progress and Account Management | P44-A4-01, P44-A4-02, P44-A4-03 |
| P45 | Help and Support | `/help` | Progress and Account Management | P45-A4-01, P45-A4-02 |
| P46 | Empty, Loading, Error and Success State Library | `Supporting design library` | Progress and Account Management | P46-A4-01, P46-A4-02, P46-A4-03, P46-A4-04, P46-A4-05, P46-A4-06, P46-A4-07, P46-A4-08, P46-A4-09, P46-A4-10, P46-A4-11, P46-A4-12, P46-A4-13, P46-A4-14, P46-A4-15 |

## Interpretation rules

- **Repository code and accepted evidence** define the current implementation.
- **This registry and its images** define the approved target user experience.
- A visible control in a prototype does not prove that its backend, route, worker, integration, or persistence layer exists.
- Do not rename page references, sheet references, page names, or target routes without explicit approval.
- When a page is implemented, record traceability from page/sheet reference to repository paths, tests, evidence, limitations, and the next gate.
