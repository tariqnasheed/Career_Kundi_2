# CareerKundi foundation migrations (0050-PF1-S1R1A)

- Schema authority: explicit Alembic revisions in this directory.
- Version table: `public.careerkundi_foundation_version`
- Do not use `Base.metadata.create_all` / `drop_all` in revisions.
- Do not import `app.db.models` / `Base` inside revision scripts.
- Legacy lineage under `app/db/migrations/` is frozen historical material.
- Autogenerate candidates must be manually reviewed before acceptance.
- Startup uses `python -m app.db.migration_runner` (settings.database_url_sync only).
