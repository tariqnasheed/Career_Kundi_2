from __future__ import annotations

ELECTRICAL_PACK = {
    "domain_terms": [
        "BS 7671",
        "safe isolation",
        "earthing",
        "insulation resistance",
        "RCD",
        "polarity",
        "Zs",
        "bonding",
    ],
    "verification_checks": [
        "confirm safe isolation before work",
        "inspect cable terminations",
        "test continuity and earthing",
        "test insulation resistance",
        "verify polarity and protective device selection",
        "record RCD trip times and Zs values",
    ],
    "safety_checks": [
        "verify earthing and bonding integrity",
        "check protective device suitability",
        "confirm isolation locks and warning notices",
    ],
    "common_mistakes": [
        "Selecting cable size only by current rating and ignoring voltage drop.",
        "Leaving loose terminations that lead to overheating.",
        "Energising circuits before polarity and continuity checks.",
    ],
    "role_specific_examples": [
        "On a six-flat conversion, I confirmed supply type, selected RCBOs, verified bonding and earthing, completed insulation resistance and RCD tests, and issued certification after all BS 7671 checks passed.",
    ],
    "interview_closings": [
        "In an interview, I would show how I deliver safe isolation, compliance evidence, and complete electrical certification.",
    ],
    "contamination_terms": ["contraindications", "allergen", "case record trail"],
}
