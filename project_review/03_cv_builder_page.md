# CV Builder Page

## Current goal

Redesign the CV Builder page and improve backend support for template-based, role-targeted CV generation.

---

## Required template count

At least **15 templates**.

---

## Required template styles

| # | Template style |
|---|----------------|
| 1 | Modern ATS |
| 2 | Classic Professional |
| 3 | Executive |
| 4 | Compact One-Page |
| 5 | Technical Engineer |
| 6 | Software Developer |
| 7 | Data/Analytics |
| 8 | Academic |
| 9 | Graduate |
| 10 | Creative Minimal |
| 11 | Elegant Serif |
| 12 | Corporate Blue |
| 13 | Healthcare Professional |
| 14 | Project Manager |
| 15 | International UK/EU Style |

---

## Required UX

- Smaller and cleaner template cards
- Template preview opens when selected
- Selected template visible in main preview area
- Profile-linked section toggles
- Custom section adding option
- Role-targeted CV mode
- Ability to include/exclude profile sections
- Ability to generate or improve individual sections
- Ability for user to add rough notes and have the model enhance them
- User should review generated sections before final CV generation
- Export buttons should be clear and not confusing

---

## Backend requirements

- CV generation should respect selected profile toggles.
- Custom sections should be preserved.
- Role-targeted generation should use selected profile material plus target role input.
- AI section improvement should not fabricate unsupported experience.
- Export should support selected template consistently.

---

## Baseline issues placeholder

_Document CV Builder issues found during review._

| ID | Area | Issue | Severity | Status |
|----|------|-------|----------|--------|
| CV-001 | Templates | Template count/styles not yet verified against 15-style list | TBD | open |
| CV-002 | UX | Section-level review flow not yet implemented | TBD | open |
| CV-003 | Export | Template consistency across PDF/DOCX export TBD | TBD | open |

---

## Sample screenshots/output placeholder

_Save artifacts under `project_review/screenshots_or_export_notes/` and `project_review/samples/`._

| Template | Screenshot | Export file | Notes |
|----------|------------|-------------|-------|
| _Modern ATS_ | `screenshots_or_export_notes/cv_modern_ats.png` | `samples/cv/cv_modern_ats.pdf` | |

---

## Next implementation notes placeholder

_Next Cursor task: CV Builder redesign (Implementation order step 6)._

- [ ] Audit current template inventory vs required 15 styles
- [ ] Redesign template picker cards and preview panel
- [ ] Add profile section toggles and custom sections
- [ ] Implement section-level generate/improve with user review step
- [ ] Capture before/after screenshots for `project_review/`
