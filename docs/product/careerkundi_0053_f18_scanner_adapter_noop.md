# 0053-F18 — Scanner Adapter Interface + No-Op Adapter

## What F18 adds

- Scanner adapter protocol/interface: `attachment_scanner_adapter.py`
- No-op unavailable adapter: `NoopUnavailableScannerAdapter`
- Factory: `get_configured_attachment_scanner_adapter()` (returns no-op only)
- Capability metadata: availability `unavailable`, capability `unavailable`
- Scan result uses F17 `ScanResultContract` with verdict `not_run`

## What F18 does not add

- Real scanner engine / worker loop / startup registration
- ClamAV / VirusTotal / third-party scanning packages or APIs
- File parsing / OCR / LLM review
- Quarantine storage movement/deletion
- Scan route/API or frontend scan controls
- Claim / evidence / review mutation
- DB migration
- Applying adapter results to the database

## Safety rules

- A no-op adapter is **not** a scanner and is **not** verification.
- The no-op adapter does **not** read file bytes, call the network, or spawn external processes.
- It must **not** return clean / safe / passed / trusted language.
- Public EvidenceRead remains `scan_not_available`.
- Future real scanner adapters require a separately approved slice.

## Behavior

| Item | Value |
|---|---|
| Adapter name | `noop_unavailable` |
| Availability | `unavailable` |
| Verdict | `not_run` |
| Safe error code | `scanner_unavailable` |
| F17 plan action | `NO_OP` (`apply_to_database=False`) |

## Next

**0053-F19**–**F20** accepted after this ladder; then **0053-F21** Local Scanner Runtime Contract Tests only after F20 acceptance.
