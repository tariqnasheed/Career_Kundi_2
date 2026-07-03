# Iteration 004E-B Job Posting Link Extraction Summary

*Captured: 2026-07-03 09:24 UTC*

## Implementation notes

- JSON-LD Schema.org `JobPosting` is parsed first when present.
- HTML heading/section fallback is used when structured data is missing.
- User-provided manual fields override extracted URL fields.
- Tests use mocked/static HTML — no live internet required.
- Live URL fetch uses manual redirect validation, DNS/IP SSRF checks, and a 2 MB response cap.
- 004F global job search remains deferred.

### Future improvements (deferred)

- Cache extraction result on saved job / pack generation to avoid repeated live fetches.
- Optional robots.txt compliance check before fetch.
- Persist merged extraction fields on saved job rows when useful.

## Sample metrics

| Sample | Extraction Method | Confidence | Extracted Fields | Warnings | Coverage Score | Added Coverage Questions | Fake URLs | Generic Phrase Hits | Silly Question Hits |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JSON-LD JobPosting | json_ld | high | 16 | 0 | 100 | 0 | 0 | 0 | 0 |
| HTML section fallback | html_sections | medium | 5 | 2 | 100 | 0 | 0 | 0 | 0 |
| Manual + URL merge | json_ld | high | 16 | 0 | N/A | 0 | 0 | 0 | 0 |

## Research-assisted development

- Primary structured source: Schema.org JobPosting JSON-LD (`application/ld+json`).
- Fallback: OpenGraph/meta tags and HTML section headings (Responsibilities, Requirements, etc.).
- SSRF safety: no automatic redirects; each hop validated; private/loopback/link-local IPs blocked.
- No fake URLs or fabricated extraction content.
