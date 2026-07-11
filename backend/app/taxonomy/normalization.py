"""
Deterministic taxonomy text normalization and source/confidence guards (0051-F1).

No LLM calls. No external APIs.
"""

from __future__ import annotations

from app.taxonomy.contracts import ConfidenceLevel, SourceType, TaxonomyMatch


def normalize_taxonomy_text(value: str) -> str:
    """Trim, collapse repeated whitespace, and lowercase for matching."""
    return " ".join((value or "").split()).strip().casefold()


def normalize_aliases(values: list[str]) -> list[str]:
    """Deduplicate aliases case-insensitively; preserve first-seen display form."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        display = " ".join((raw or "").split()).strip()
        if not display:
            continue
        key = display.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(display)
    return out


def validate_source_confidence(source: SourceType, confidence: ConfidenceLevel) -> None:
    """
    Reject unsafe source/confidence combinations.

    - model_inferred must not be verified
    - fallback_default must not be verified
    - unknown source requires unknown confidence
    """
    if source == SourceType.MODEL_INFERRED and confidence == ConfidenceLevel.VERIFIED:
        raise ValueError("model_inferred must not be returned as verified")
    if source == SourceType.FALLBACK_DEFAULT and confidence == ConfidenceLevel.VERIFIED:
        raise ValueError("fallback_default must not be returned as verified")
    if source == SourceType.UNKNOWN and confidence != ConfidenceLevel.UNKNOWN:
        raise ValueError("unknown source must map to unknown confidence")


def safe_default_source(value: str | None) -> SourceType:
    """Map empty/missing text to unknown; non-empty free text to user_provided."""
    if value is None or not str(value).strip():
        return SourceType.UNKNOWN
    return SourceType.USER_PROVIDED


def _coerce_safe_confidence(source: SourceType, confidence: ConfidenceLevel) -> ConfidenceLevel:
    """Downgrade illegal verified claims; default unknown source → unknown confidence."""
    if source == SourceType.UNKNOWN:
        return ConfidenceLevel.UNKNOWN
    if source == SourceType.MODEL_INFERRED and confidence == ConfidenceLevel.VERIFIED:
        return ConfidenceLevel.INFERRED
    if source == SourceType.FALLBACK_DEFAULT and confidence == ConfidenceLevel.VERIFIED:
        return ConfidenceLevel.DEFAULT
    return confidence


def build_taxonomy_match(
    input_text: str,
    matched_role_id: str | None,
    source: SourceType,
    confidence: ConfidenceLevel,
    explanation: str,
) -> TaxonomyMatch:
    """Build a TaxonomyMatch with safe confidence coercion for inferred/fallback sources."""
    safe_confidence = _coerce_safe_confidence(source, confidence)
    validate_source_confidence(source, safe_confidence)
    return TaxonomyMatch(
        input_text=(input_text or "").strip(),
        normalized_text=normalize_taxonomy_text(input_text),
        matched_role_id=matched_role_id,
        source=source,
        confidence=safe_confidence,
        explanation=(explanation or "").strip(),
    )
