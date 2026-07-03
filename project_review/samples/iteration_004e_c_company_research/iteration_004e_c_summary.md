# Iteration 004E-C Company Profile and Source-Cited Research Summary

*Captured: 2026-07-03 10:24 UTC*

## Implementation notes

- Company research priority: user profile → job posting derived → official company page → meta/HTML fallback.
- Schema.org Organization JSON-LD (`Corporation`, `LocalBusiness`, etc.) is parsed when present.
- HTML section headings (About, Products, Services, Industries, Markets, Mission) provide fallback context.
- Source URLs are real input/captured URLs only — no fabricated citations.
- Safe fetch reuses 004E-B SSRF redirect validation, DNS/IP checks, and 2 MB response cap.
- Model knowledge remains disabled; 004F global job search remains deferred.

## Sample metrics

| Sample | Research Method | Confidence | Company Facts | Source URLs | Warnings | Company Questions Added | Fake URLs | Generic Phrase Hits | Silly Question Hits |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Organization JSON-LD | json_ld_organization | high | 6 | 2 | 0 | 4 | 0 | 0 | 0 |
| HTML section fallback | html_sections | medium | 5 | 1 | 1 | 0 | 0 | 0 | 0 |
| Manual profile override | json_ld_organization | high | 6 | 2 | 0 | 0 | 0 | 0 | 0 |

## Research-assisted development

- Primary structured source: Schema.org Organization JSON-LD (`application/ld+json`).
- Useful fields: name, legalName, description, url, sameAs, location, areaServed, makesOffer, knowsAbout.
- Fallback: OpenGraph/meta tags and HTML section headings.
- No fake URLs or fabricated company facts.
