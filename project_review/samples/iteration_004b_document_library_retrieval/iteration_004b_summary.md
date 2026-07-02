# Iteration 004B Document Library Retrieval Summary

*Captured: 2026-07-02 22:48 UTC*

## Goal

Retrieve and use saved role-pack material from `documents/interview_packs/` as supporting study-module sources.

## 004B-S stabilization notes

- Matching threshold tightened: document library is marked `used` only with strong skill-tag overlap, two or more meaningful skill overlaps, or meaningful question-text overlap — not merely because a role folder exists.
- HR/behavioral/role-specific questions no longer automatically mark document library as `used`; they remain `available_not_used` unless the saved material directly matches the prompt.
- Short, heading-only, and generic process snippets are filtered out (minimum useful snippet length enforced).
- Supporting focus text is generated from matched skills and question terms rather than random generic sentences.

## 004B-F polish notes

004B-F: Generic Core Terminology-only matches are now treated as `available_not_used` instead of `used`.

- `Core Terminology` alone cannot mark document library as used.
- Generic core-terminology snippets (e.g. `Core terminology for Core Terminology`) are filtered out.
- Showcase support examples prefer substantive technical matches (AWS/Kubernetes/CI/CD, medication review, espresso/hygiene).

## 004B-G polish notes

004B-G: Generic Role Specific snippets are filtered, and technical skill labels are normalized.

- Role Specific / intermediate quality checks / structured verification snippets are rejected.
- Matched skill labels render as `AWS`, `CI/CD`, `SQL`, `HACCP`, etc.
- Showcase support blocks must include substantive snippet text without generic placeholders.

## Quality table

| Role | Questions | Study Material Present | Source Metadata Present | Document Library Used | Document Library Available Not Used | Local Fallback Used | Fake URLs Found | Answers Over 500 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Data Analyst | 35 | 35 | 35 | 0 | 0 | 35 | 0 | 0 |
| Electrical Engineer | 35 | 35 | 35 | 0 | 35 | 35 | 0 | 0 |
| Clinical Pharmacist | 36 | 36 | 36 | 26 | 10 | 36 | 0 | 0 |
| Barista | 32 | 32 | 32 | 23 | 9 | 32 | 0 | 0 |
| DevOps Engineer | 36 | 36 | 36 | 0 | 36 | 36 | 0 | 0 |

## Example document-library source block

```markdown
### Source / fallback status
- **Used:** Document-library role material; Local deterministic study material
- **Web research:** Not configured in this iteration — Web research retrieval is not configured in this iteration.
- **Model knowledge:** Not configured in this iteration — Model knowledge retrieval is not enabled in deterministic mode.
- **Document library:** Used — matched saved role-pack material from `documents/interview_packs/healthcare/clinical_pharmacist/structured_content.json` — Matched saved role-pack material for Clinical Pharmacist using skill overlap: Pharmacology.

_Generated from document library, local deterministic study material. web research and model knowledge retrieval are not configured._
```

## Example document-library support section

```markdown
### Document-library support
Saved project material matched this question through role/skill overlap.

- Source: `documents/interview_packs/technology/barista/structured_content.json`
- Matched skills: Coffee Preparation, Customer Service
- Supporting focus: espresso consistency, grind and dose control, queue management, order accuracy
- Snippet: Coffee Preparation means carrying out the task safely and correctly from preparation to final verification. At beginner level, focus on what the task is, where risk appears first, and what minimum checks must be…
- Snippet: Whether the candidate can explain Coffee Preparation with method, standards, and safety checks.
```

## Retrieval quality observations

- **Worked well:** Technical/skill-tagged questions with real overlap (AWS, Kubernetes, cable sizing, medication review, espresso preparation) receive compact support snippets and skill-linked supporting focus.
- **Weak / absent:** Data Analyst has no saved role pack in the document library, so `document_library` remains `not_configured`.
- **HR / generic prompts:** Usually remain `available_not_used` with an explicit note that saved material exists but no question-specific match was strong enough.
- **Usefulness:** Support sections add transparent pointers to saved structured JSON without duplicating full legacy packs or attaching generic boilerplate.

## Remaining for Iteration 004C

- Add model-knowledge study synthesis behind a feature flag (recommended next step).
- Optional later: web-research agent stub with real captured URLs only.
- Improve cross-question deduplication of document-library snippets.

