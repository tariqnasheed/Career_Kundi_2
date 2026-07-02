# Iteration 002 Baseline Summary

*Captured: 2026-07-02 20:09 UTC*

## Generation method

- Script: `backend/scripts/generate_baseline_interview_samples.py`
- Functions: `mock_generate_questions`, `build_role_overview`, `build_interview_pack_markdown`, `build_study_material_markdown`
- Production logic changed: **no** (capture-only helper script and review docs)

## Sample files generated

- `project_review/samples/iteration_002_baseline/data_analyst_interview_pack.md`
- `project_review/samples/iteration_002_baseline/data_analyst_study_only.md`
- `project_review/samples/iteration_002_baseline/electrical_engineer_interview_pack.md`
- `project_review/samples/iteration_002_baseline/electrical_engineer_study_only.md`
- `project_review/samples/iteration_002_baseline/clinical_pharmacist_interview_pack.md`
- `project_review/samples/iteration_002_baseline/clinical_pharmacist_study_only.md`
- `project_review/samples/iteration_002_baseline/barista_interview_pack.md`
- `project_review/samples/iteration_002_baseline/barista_study_only.md`
- `project_review/samples/iteration_002_baseline/devops_engineer_interview_pack.md`
- `project_review/samples/iteration_002_baseline/devops_engineer_study_only.md`
- `project_review/samples/iteration_002_baseline/baseline_summary.md`
- `project_review/samples/iteration_002_baseline/metrics.json`

## Metrics table

| Role | Questions generated | Categories covered | Skills covered | Study material present for every question | Average answer word count | Max answer word count | Answers over 500 words | Study modules with visible sections | Generic phrases noticed | Missing coverage noticed |
|---|---|---|---|---|---|---|---|---|---|---|
| Data Analyst | 29 | behavioral, role_specific, technical | Core terminology, Dashboarding, Data Quality, Excel, SQL | yes | 165.5 | 271 | 0 | 29 | 0 | HR questions; daily routine questions; responsibility-specific questions; company-specific questions |
| Electrical Engineer | 28 | behavioral, role_specific, technical | Cable Sizing, Commissioning, Core terminology, Electrical Installation, Load Calculations | yes | 158.8 | 237 | 0 | 28 | 0 | HR questions; daily routine questions; responsibility-specific questions; tool/software questions; company-specific questions |
| Clinical Pharmacist | 28 | behavioral, role_specific, technical | Clinical Governance, Core terminology, Medication Review, Patient Counselling, Pharmacology | yes | 153.2 | 213 | 0 | 28 | 0 | HR questions; daily routine questions; responsibility-specific questions; tool/software questions; company-specific questions |
| Barista | 24 | behavioral, role_specific, technical | Coffee Preparation, Core terminology, Customer Service, HACCP, Stock Control | yes | 154.5 | 214 | 0 | 24 | 0 | HR questions; daily routine questions; tool/software questions; seniority variations; company-specific questions |
| DevOps Engineer | 32 | behavioral, role_specific, technical | AWS, CI/CD, Core terminology, Docker, Kubernetes, Monitoring | yes | 172.3 | 225 | 0 | 32 | 0 | HR questions; daily routine questions; responsibility-specific questions; company-specific questions |

## Job Search / Interview Pack observations

Honest read of the five captured packs:

- **Present today:** behavioral prompts tied to responsibilities; technical/skill-tagged compiler questions; some scenario/calculation/terminology variants; role-specific motivation prompt; standards/safety language in technical answers for engineering/healthcare/hospitality.
- **Weak or missing today:** explicit HR category questions; dedicated daily-routine/day-one prompts; case-study category; seniority-tier question sets (junior vs senior); company-specific questions without company data; breadth across every listed requirement skill (focus skill drives most technical depth).
- **Answer shape:** technical answers are substantially richer than behavioral STAR answers, which are often short template paragraphs.
- **Export structure:** role overview, employer expectations, skill map, per-question study block, model answer, and follow-ups are present in Markdown exports.

## Study Material observations

- **Question-specific modules exist** for every exportable question in all five snapshots.
- **Structured sections** (`Core idea`, `How to apply it`, `Common mistakes`, `Interview tip`) appear in exported Markdown for compiler-backed technical questions.
- **Behavioral / motivation modules** reuse STAR-prep framing; they are question-linked but less technically deep.
- **No source ladder metadata** (web/model/library/fallback) is exposed in study modules.
- **Beginner/intermediate/advanced depth** is present in compiler study objects but export rendering compresses some modules visually.
- **Not yet real multi-source learning material** — deterministic compiler/fallback content only.

## Biggest baseline weaknesses

- No explicit HR question category in generated packs.
- Limited seniority variation (few dedicated junior/senior prompts per pack).
- Behavioral answers are often short (~40–80 words) compared with technical compiler answers.
- Requirement skills beyond the primary focus skill get uneven technical question coverage.
- No company-specific block unless company data is supplied.
- Study material lacks cited sources and fallback-status transparency.
- Daily routine / day-one operational questions are sparse or absent.
- Case-study category not consistently represented.
- Short behavioral answers observed in: Data Analyst, Electrical Engineer, Clinical Pharmacist, Barista, DevOps Engineer.

## Next recommended implementation step

Proceed to **Implementation order step 3 — Job Search + Interview Pack Generator fixes**: decouple popular-role auto-export on the frontend, improve job-import field coverage, and expand question generation templates for HR/daily-routine/seniority variants before further study-material architecture work.

