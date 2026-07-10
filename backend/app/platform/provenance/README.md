# CareerKundi provenance domain (0050-PF4-S1)

## Owns

- `SourceRef` / `SnapshotRef` — durable addressing
- `SourceKind` — approved source ladder kinds
- `SourceRecord` / `SourceSnapshot` persistence + create/read service helpers

## Does not own

- Claims, evidence, verification
- Passport / profile biography
- Crawlers, file stores, document parsers
- Public FastAPI routes (PF4-S1)
- Taxonomy, geo, consent

## Semantics

| Concept | Meaning |
|---------|---------|
| Source | Origin or channel of information |
| Snapshot | Captured observation of a source at a point in time |
| Claim | Statement about a subject (PF5+) |
| Evidence | Material supporting/contesting a claim (later) |

**Source ≠ Snapshot.** A source may have many snapshots. A snapshot belongs to exactly one source. A URL/source row alone is not proof of observed content at a time.
