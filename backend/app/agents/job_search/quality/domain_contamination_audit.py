from __future__ import annotations

DOMAIN_CONTAMINATION_RULES = {
    "healthcare": [
        "conductor",
        "termination",
        "earth fault loop impedance",
        "rcd",
        "consumer unit",
        "cable route",
    ],
    "hospitality": [
        "conductor",
        "earth fault loop impedance",
        "bs 7671",
        "patient baseline",
        "sbar",
        "case record trail",
    ],
    "public_administration": [
        "conductor",
        "termination",
        "rcd",
        "milk texture",
        "contraindications",
    ],
    "architecture": [
        "earth fault loop impedance",
        "rcd testing",
        "patient deterioration",
        "allergen controls",
    ],
}


def domain_contamination_count(text: str, role_family: str) -> int:
    lowered = (text or "").lower()
    blocked = DOMAIN_CONTAMINATION_RULES.get(role_family, [])
    return sum(1 for term in blocked if term in lowered)


def has_domain_contamination(text: str, role_family: str) -> bool:
    return domain_contamination_count(text, role_family) > 0
