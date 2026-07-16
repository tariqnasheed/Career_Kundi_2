# 0053-F15 — Runtime Badge-Seed Startup Reliability Fix

## What F15 fixes

- Badge catalogue seed no longer does per-badge round trips on every boot
- Skip-safe when catalogue rows already match seed data (no commit)
- Lifespan wraps badge seed in `asyncio.wait_for` (15s) so a stalled DB cannot block OpenAPI forever
- Startup continues after badge-seed timeout/failure with a clear warning log

## What F15 does not change

- No new badge product features
- No evidence / verification / review / Passport behavior
- No claim status mutation
- No scan queue / malware scanning
- No OCR / parsing / LLM provider changes
- No public sharing
- No DB migration / destructive DB operations

## Root cause

`main.py` lifespan blocked `yield` on `seed_badge_definitions`, which issued ~39 sequential `db.get` calls and always rewrote mutable fields. With `APP_DEBUG` SQL echo against `careerkundi_f4`, local review scripts often treated this as a uvicorn/OpenAPI timeout.

## Next

**0053-F16** Attachment Scan Queue Skeleton — accepted after this ladder; then **0053-F17** Scan Worker Planning / Quarantine Policy only.
