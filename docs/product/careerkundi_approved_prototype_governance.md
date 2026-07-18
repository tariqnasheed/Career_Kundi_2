# CareerKundi Approved Prototype Governance Contract

## 1. Authority order

For any CareerKundi task, use this order of authority:

1. The user's latest explicit approval or scope instruction.
2. Accepted repository evidence and committed code.
3. The live tracker, master build plan, phase plan, report and phase evidence.
4. This approved P01-P46 prototype as the target UX contract.
5. General implementation recommendations.

Never overwrite an accepted repository fact with an assumption inferred from an image.

## 2. Four-state implementation vocabulary

Use these labels consistently:

- `EVIDENCE_BACKED_CURRENT`: confirmed current path or behaviour.
- `UNVERIFIED_CURRENT`: claimed or possible current path/behaviour not yet confirmed.
- `APPROVED_DESIGN_TARGET`: approved prototype behaviour or appearance.
- `CREATE_REQUIRED`: target element has no confirmed current implementation.

For technical path planning, `PROPOSED_TARGET` may be used for a specific future path.

## 3. Prototype reading procedure

Before planning or changing a feature:

1. Read `CareerKundi_Complete_Interface_Image_Index.md`.
2. Identify the relevant permanent page references and sheet references.
3. Read only the relevant page folder images, plus directly related empty/error/success states in P46.
4. Read the current repository route, component, API, model, service, tests and product documentation.
5. Create a Prototype Impact Matrix before editing code.
6. State what is current, what is target, what is absent, and what is out of scope.
7. Implement only the approved phase slice.
8. Update documentation and evidence only after tests and review pass.

Do not load all 135 images into one model context. Use the manifest and page index to select relevant sheets.

## 4. Prototype Impact Matrix

Every substantive phase touching product behaviour must contain:

| Field | Required content |
|---|---|
| Phase | Current phase/slice |
| Page references | Pxx references affected |
| Sheet references | Pxx-A4-xx references affected |
| Current routes | Evidence-backed current routes |
| Current repository paths | Evidence-backed paths only |
| Approved target | Exact prototype behaviour being targeted |
| Delta | What differs between current and target |
| Backend dependencies | Existing, absent, proposed |
| Privacy/security boundary | Owner scoping, verification, evidence and data rules |
| Tests | Unit, integration, frontend, browser and regression gates |
| Known limitations | Explicitly preserved limitations |
| Next gate | What approval is required next |

## 5. Non-negotiable product boundaries

- Evidence upload, attachment, linking and private review do not equal independent verification.
- Malware scanning is an attachment-safety concern, not evidence verification.
- Claim `support_status` and `verification_status` must not be silently changed by attachment-scan operations.
- Review requests remain private and must not be treated as certification.
- CareerKundi badges represent platform progress, not external credentials.
- No job, admission, scholarship, visa, immigration or employment outcome is guaranteed.
- No unrestricted scraping, public evidence sharing, wallet, DID or blockchain behaviour may be inferred from the prototype.
- No scanner, worker, scheduler, quarantine, audit, admin or frontend status UI may be claimed as implemented unless repository evidence proves it.
- Avoid fake integrations, fake status values and decorative controls that cannot perform their stated action.

## 6. Change control

- Never implement multiple future phases merely because the prototype displays them.
- Never redesign an approved page during an unrelated backend phase.
- Never create backend behaviour solely to make an image appear implemented.
- Reuse existing repository patterns before creating new abstractions.
- Preserve unrelated local work.
- Stage exact files only.
- Do not stage `.env`, `backend/.env`, `backend/data/knowledge_graph.gpickle` or unapproved `documents/` content.
- Do not commit or push until the task explicitly authorises it.
- Stop at the named gate.

## 7. Master Implementation Ladder

Maintain the live implementation ladder with at least:

- phase
- purpose
- status
- dependencies
- approved decisions
- implemented files
- tests/evidence
- known limitations
- relevant prototype references
- next gate

The prototype is a long-term target map. The implementation ladder is the execution truth.
