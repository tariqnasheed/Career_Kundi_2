# 0053-F21 — Local Scanner Runtime Safety Contract

## What F21 adds

- Runtime safety policy module: `attachment_scanner_runtime_policy.py`
- Disabled-by-default runtime guard (`LOCAL_SCANNER_RUNTIME_ENABLED=False`)
- No-shell / no-network scanner policy declarations
- Bounded timeout constants (default 30s, max 120s)
- Safe error code/message normalization and path/URI redaction helpers
- Empty allowed-binary list (inactive; does not imply a live scanner)

## What F21 does not add

- Real scanner command execution / process spawning
- ClamAV / VirusTotal / scanner packages
- File parsing / OCR / LLM review
- Worker loop / scheduler / startup registration
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- Claim / evidence / review mutation
- DB migration
- Env/config toggles that enable scanning
- Command runner or binary path lookup

## Decision

| Item | Value |
|---|---|
| Runtime enabled | `False` |
| Shell execution | disallowed |
| Network scanner | disallowed |
| Raw output to user | disallowed |
| Allowed binaries | empty |
| Active factory adapter | `noop_unavailable` |
| Disabled local adapter | still disabled / not selected |

## Safety rules

- A runtime contract is **not** scanner execution and is **not** verification.
- Never expose raw filesystem paths, storage URIs, or raw scanner dumps to users.
- Future real scanner implementation requires a separately approved slice.

## Next

**0053-F22** Scanner Result Persistence Guard — accepted after F21; then **0053-F23** Quarantine Storage Planning only after F22 acceptance.
