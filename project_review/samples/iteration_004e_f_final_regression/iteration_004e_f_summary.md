<!-- careerkundi-run-manifest {"audit_schema_version": "a5cfec07014c", "dirty_worktree_fingerprint": "eac3f6561de1249e", "document_library_fingerprint": "464788207deefbce", "findings_schema_version": "2", "generated_at": "2026-07-07T22:40:47Z", "git_head": "d27d15732b970c24fa72108831b80fb58ba8b3fb", "manifest_version": 1, "metrics_schema_version": "2", "run_id": "run-20260707T224047Z-e39c62ea", "work_plan_digest": "2942fe9ae8d7244b"} -->
# Iteration 004E-F Final Regression Gate Summary

*Captured: 2026-07-07T22:40:47Z*

*Run: `run-20260707T224047Z-e39c62ea` — HEAD `d27d1573`, worktree `eac3f6561de1249e`, audit schema `a5cfec07014c`*

## Purpose

Final verification/stabilization for Interview Pack Generator and Interview Study Material.
Interview Pack Generator + Interview Study Material core pipeline is regression-checked.
Includes 004E-E2 adaptive study-material depth and length policy checks.
Includes 004E-E2.2 semantic integrity, claim integrity, and truthful regression gates.

## Risk controls (004E-F)

1. **Fake completion risk** — gate requires zero missing answers/study modules and clean quality metrics before claiming completion.
2. **Generic content risk** — blocked-phrase scan covers answers and study material, not just question titles.
3. **Thin input risk** — title-only sample must not claim fake full coverage (coverage score 0).
4. **Source-ladder regression risk** — user fields, URL extraction, company research, document library, model status, and fallback statuses remain transparent.
5. **Study material regression risk** — every exportable question has a dedicated module; duplicate fingerprint scan uses full module content.
6. **Export regression risk** — markdown export keeps model answer and study material attached per question.
7. **Frontend/backend drift risk** — no schema changes in this phase; prior 004E-E alignment preserved.
8. **Security/network risk** — no new direct live fetching; samples and tests use mocked/deterministic inputs only.
9. **Over-scope risk** — 004F global job search not implemented; role catalog dropdown not implemented; Final Content Library Regeneration not run.
10. **Overfitting risk** — five deterministic random roles (fixed seed list) supplement ten fixed cross-sector roles.

## Deferred

- **004F** global job search remains deferred.
- **Role catalog dropdown** remains deferred (next UI improvement before or alongside 004F planning).
- **Final Content Library Regeneration** not run in this phase.

## Sample metrics

| Sample | Role | Input Type | Questions | Answers | Study Modules | Missing Answers | Missing Study Modules | Coverage Score | Source Ladder Present | Export Ready | Hard Max Violations | Fake URLs | Generic Hits | Silly Hits | Empty Sections | Duplicate Study Modules | Internal Label Leaks |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| Data Analyst | Data Analyst | rich_description | 26 | 26 | 26 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Electrical Engineer | Electrical Engineer | rich_responsibilities_tools | 35 | 35 | 35 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Clinical Pharmacist | Clinical Pharmacist | rich_healthcare | 36 | 36 | 36 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Barista | Barista | document_library | 27 | 27 | 27 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Teaching Assistant | Teaching Assistant | education | 27 | 27 | 27 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Financial Analyst | Financial Analyst | finance | 26 | 26 | 26 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| DevOps Engineer | DevOps Engineer | technical | 30 | 30 | 30 | 0 | 0 | 82 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| MEP Site Engineer | MEP Site Engineer | construction | 15 | 15 | 15 | 0 | 0 | 86 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Social Media Creator | Social Media Creator | creative_odd_job | 28 | 28 | 28 | 0 | 0 | 86 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Delivery Driver | Delivery Driver | part_time_odd_job | 14 | 14 | 14 | 0 | 0 | 86 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Title only | Mystery Role | title_only | 9 | 9 | 9 | 0 | 0 | 0 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rich source ladder | Data Analyst | rich_source_ladder | 34 | 34 | 34 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Document export | Data Analyst | document_export | 34 | 34 | 34 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Part-time odd job | Weekend Barista | part_time_odd_job | 20 | 20 | 20 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lab Technician | Lab Technician | science | 15 | 15 | 15 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Logistics Coordinator | Logistics Coordinator | office_business | 15 | 15 | 15 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| HR Assistant | HR Assistant | office_business | 27 | 27 | 27 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Graphic Designer | Graphic Designer | creative | 27 | 27 | 27 | 0 | 0 | 100 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Warehouse Picker | Warehouse Picker | part_time_odd_job | 14 | 14 | 14 | 0 | 0 | 86 | yes | yes | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Deterministic random regression samples

Fixed deterministic set (seed list of 15 roles; 5 selected):

- Lab Technician (science/health)
- Logistics Coordinator (office/business)
- HR Assistant (office/business)
- Graphic Designer (creative/media)
- Warehouse Picker (part-time/odd-job style)

| Role | Input Type | Questions | Missing Answers | Missing Study Modules | Fake URLs | Generic Hits | Silly Hits |
|---|---|---:|---:|---:|---:|---:|---:|
| Lab Technician | science | 15 | 0 | 0 | 0 | 0 | 0 |
| Logistics Coordinator | office_business | 15 | 0 | 0 | 0 | 0 | 0 |
| HR Assistant | office_business | 27 | 0 | 0 | 0 | 0 | 0 |
| Graphic Designer | creative | 27 | 0 | 0 | 0 | 0 | 0 |
| Warehouse Picker | part_time_odd_job | 14 | 0 | 0 | 0 | 0 | 0 |

## Aggregate quality findings

- All samples clean: **False**
- Missing answers (total): **0**
- Missing study modules (total): **0**
- Fake URLs (total): **0**
- Generic hits (total): **0**
- Silly hits (total): **0**
- Empty sections (total): **0**
- Hard max violations (total): **0**
- Duplicate study modules (total): **0**
- Internal label leaks (total): **0**
- Unsupported personal claims (total): **0**
- Unsupported numeric claims (total): **0**
- Cross-domain contamination hits (total): **0**
- Surface quality defects (total): **0**
- Thin-input specificity violations (total): **0**
- Structure-incomplete study modules (total): **0**
- Substantive-depth failures (total): **0**

## Failing samples (per-sample reasons)

- **DevOps Engineer** (DevOps Engineer): generic_template_saturation_failure_count

## Quality gates

In-generator deterministic gates (missing-content, blocked-phrase, fake-URL, silly-question, claim-integrity, surface-quality, cross-domain, structural/substantive depth) are computed by `audit_generated_pack` and reflected in the metrics above. External live-network and secret scans are NOT executed by this script and remain pending as a separate step.
