# Iteration 003 Interview Pack Fix Summary

*Captured: 2026-07-02 20:27 UTC*

## Generation method

- Script: `backend/scripts/generate_iteration_003_samples.py`
- Functions: `mock_generate_questions`, `apply_coverage_plan`, `build_role_overview`, `build_interview_pack_markdown`
- Production logic changed: **yes** (coverage planner, HR/daily-routine categories, behavioral answer expansion, frontend flow)

## Iteration 002 vs 003 comparison

| Role | Iteration 002 Questions | Iteration 003 Questions | HR Present | Daily Routine Present | Seniority Present | Case/Practical Present | Skills Covered Better? | Answers Over 500 |
|---|---|---|---|---|---|---|---|---|
| Data Analyst | 29 | 35 | yes | yes | yes | yes | yes | 0 |
| Electrical Engineer | 28 | 36 | yes | yes | yes | yes | yes | 0 |
| Clinical Pharmacist | 28 | 36 | yes | yes | yes | yes | yes | 0 |
| Barista | 24 | 34 | yes | yes | yes | yes | yes | 0 |
| DevOps Engineer | 32 | 37 | yes | yes | yes | yes | yes | 0 |

## What improved

- Explicit `hr` and `daily_routine` question categories
- Seniority-tier prompts (junior/mid/senior)
- Case-study and practical-task questions
- Tool/software and standards/safety coverage gaps filled
- Behavioral STAR answers expanded (typically 120+ words)
- Popular role selection no longer auto-generates on frontend
- Company name optional for generation

## What remains weak

- Study material still deterministic/compiler-only (no source ladder)
- Some HR answers use placeholder brackets for notice period
- Live LLM path may not yet mirror all mock coverage rules
- Frontend download still only in pack preview section

## Strong question example per role

- **Data Analyst:** Explain SQL to a junior engineer and include trade-offs in production systems and one measurable quality signal.…
- **Electrical Engineer:** Explain Electrical Installation to an apprentice and include how you verify compliance to standards (e.g. BS 7671 (IET Wiring Regulations)).…
- **Clinical Pharmacist:** As a Clinical Pharmacist, explain Pharmacology to a newly qualified clinician and include clinical safety checks tied to GHS/CLP.…
- **Barista:** If a new hire joined your Barista function while handling 'Espresso preparation, milk steaming, and drink consistency during rush hours', how would you break do…
- **DevOps Engineer:** Explain AWS to a junior engineer and include trade-offs in production systems and one measurable quality signal.…

## Still-weak question example per role

- **Data Analyst:** Why are you applying for this Data Analyst position, and what makes you a strong fit for our team?…
- **Electrical Engineer:** Why are you applying for this Electrical Engineer position, and what makes you a strong fit for our team?…
- **Clinical Pharmacist:** Why are you applying for this Clinical Pharmacist position, and what makes you a strong fit for our team? In this role-specific case, address: Clinical Pharmaci…
- **Barista:** Why are you applying for this Barista position, and what makes you a strong fit for our team?…
- **DevOps Engineer:** Why are you applying for this DevOps Engineer position, and what makes you a strong fit for our team?…

## Next recommended step

Proceed to **Study Material multi-source architecture** (Implementation order step 4) after validating frontend workflow in manual QA.

