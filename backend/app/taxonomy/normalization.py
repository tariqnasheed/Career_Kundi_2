"""
Deterministic taxonomy text normalization and source/confidence guards (0051-F1/F2).

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

    - model_inferred / fallback_default / user_provided / external_taxonomy_reference
      must not be verified (no official verification path in F1/F2)
    - unknown source requires unknown confidence
    """
    if confidence == ConfidenceLevel.VERIFIED and source in {
        SourceType.MODEL_INFERRED,
        SourceType.FALLBACK_DEFAULT,
        SourceType.USER_PROVIDED,
        SourceType.EXTERNAL_TAXONOMY_REFERENCE,
    }:
        raise ValueError(f"{source.value} must not be returned as verified")
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
    if confidence != ConfidenceLevel.VERIFIED:
        return confidence
    if source == SourceType.MODEL_INFERRED:
        return ConfidenceLevel.INFERRED
    if source == SourceType.FALLBACK_DEFAULT:
        return ConfidenceLevel.DEFAULT
    if source in {SourceType.USER_PROVIDED, SourceType.EXTERNAL_TAXONOMY_REFERENCE}:
        return ConfidenceLevel.SUGGESTED
    return confidence


def build_taxonomy_match(
    input_text: str,
    matched_role_id: str | None,
    source: SourceType,
    confidence: ConfidenceLevel,
    explanation: str,
    *,
    matched_skill_id: str | None = None,
) -> TaxonomyMatch:
    """Build a TaxonomyMatch with safe confidence coercion for unsafe verified claims."""
    safe_confidence = _coerce_safe_confidence(source, confidence)
    validate_source_confidence(source, safe_confidence)
    return TaxonomyMatch(
        input_text=(input_text or "").strip(),
        normalized_text=normalize_taxonomy_text(input_text),
        matched_role_id=matched_role_id,
        matched_skill_id=matched_skill_id,
        source=source,
        confidence=safe_confidence,
        explanation=(explanation or "").strip(),
    )
