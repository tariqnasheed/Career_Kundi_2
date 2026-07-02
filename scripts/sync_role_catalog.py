#!/usr/bin/env python3
"""Sync backend/app/data/popular_roles_catalog.json from frontend role definitions."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TS = ROOT / "frontend" / "src" / "lib" / "popularJobRoles.ts"
OUT = ROOT / "backend" / "app" / "data" / "popular_roles_catalog.json"

pat = re.compile(
    r'role\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"(full_time|part_time_odd)"\s*,\s*\[(.*?)\]\s*,\s*\[(.*?)\]\s*,\s*\[(.*?)\]\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)',
    re.DOTALL,
)


def parse_arr(s: str) -> list[str]:
    return [x.strip().strip('"') for x in re.findall(r'"([^"]+)"', s)]


def main() -> None:
    text = TS.read_text(encoding="utf-8")
    roles = []
    for m in pat.finditer(text):
        roles.append({
            "id": m.group(1),
            "title": m.group(2),
            "stream_id": m.group(3),
            "category": m.group(4),
            "skills": parse_arr(m.group(5)),
            "responsibilities": parse_arr(m.group(6)),
            "requirements": parse_arr(m.group(7)),
            "employment_type": m.group(8),
            "experience_level": m.group(9),
        })
    OUT.write_text(json.dumps(roles, indent=2), encoding="utf-8")
    print(f"Wrote {len(roles)} roles to {OUT}")


if __name__ == "__main__":
    main()
