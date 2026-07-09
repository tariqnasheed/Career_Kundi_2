from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def exact_discovery_source_url_key(
    source_url: object,
) -> str | None:
    """
    Return the conservative exact-match key for a discovery URL.

    B2.2 intentionally performs no canonicalization beyond trimming
    outer whitespace. Query strings, fragments, path casing, schemes,
    hosts, and trailing slashes remain distinct.
    """
    if not isinstance(source_url, str):
        return None

    key = source_url.strip()
    return key or None


def suppress_duplicate_discovery_results(
    results: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Suppress later duplicate discovery hits by exact trimmed source URL.

    The first keyed result wins and provider order is preserved. Results
    without a usable string URL are retained because exact URL identity
    cannot be established for them.

    Input dictionaries are not mutated. A shallow copy is created only
    when the retained source URL needs outer-whitespace trimming.
    """
    deduplicated: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for result in results:
        key = exact_discovery_source_url_key(
            result.get("source_url"),
        )

        if key is None:
            deduplicated.append(result)
            continue

        if key in seen_keys:
            continue

        seen_keys.add(key)

        if result.get("source_url") == key:
            deduplicated.append(result)
            continue

        normalized_result = dict(result)
        normalized_result["source_url"] = key
        deduplicated.append(normalized_result)

    return deduplicated
