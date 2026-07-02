#!/usr/bin/env python3
"""
Pre-generate interview packs for all popular roles into documents/interview_packs/.

Usage:
  cd backend && uv run python -m scripts.seed_role_packs
  cd backend && uv run python -m scripts.seed_role_packs --force
"""

from __future__ import annotations

import argparse
import json
import sys

from app.services.role_pack_library import (
    ensure_library_layout,
    list_library_roles,
    regenerate_pdfs_for_catalog,
    seed_catalog_role_packs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed role-pack document library")
    parser.add_argument("--force", action="store_true", help="Regenerate even if pack exists")
    parser.add_argument("--all", action="store_true", help="Regenerate all (alias for --force)")
    parser.add_argument("--pdf-only", action="store_true", help="Regenerate PDFs from saved structured JSON")
    args = parser.parse_args()

    ensure_library_layout()
    before = len(list_library_roles())
    print(f"Library roles before: {before}")

    if args.pdf_only:
        stats = regenerate_pdfs_for_catalog(only_missing=not args.force)
        print(json.dumps(stats, indent=2))
        return 0 if not stats.get("failed") else 1

    stats = seed_catalog_role_packs(force=args.force or args.all, only_missing=not (args.force or args.all))
    after = len(list_library_roles())

    print(json.dumps({**stats, "library_roles_after": after}, indent=2))
    if stats.get("failed"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
