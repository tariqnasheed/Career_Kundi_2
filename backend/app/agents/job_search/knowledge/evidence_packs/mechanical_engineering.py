from __future__ import annotations

MECHANICAL_ENGINEERING_PACK = {
    "domain_terms": [
        "heat load",
        "airflow",
        "duct sizing",
        "commissioning",
        "psychrometrics",
        "fan selection",
        "pressure drop",
        "balancing",
    ],
    "verification_checks": [
        "calculate design heat load and airflow requirements",
        "verify duct sizing and pressure drop assumptions",
        "check equipment selection against design conditions",
        "confirm commissioning readings against specification",
    ],
    "safety_checks": [
        "verify ventilation and combustion safety requirements",
        "confirm access and maintenance clearances",
        "escalate design deviations before installation",
    ],
    "common_mistakes": [
        "Sizing ducts without checking available static pressure.",
        "Ignoring infiltration and diversity factors in load calculations.",
        "Commissioning without documented balancing results.",
    ],
    "role_specific_examples": [
        "For example, on an office HVAC retrofit, I recalculated heat load, resized supply ducts for target airflow, supervised balancing, and achieved commissioning readings within 5% of design.",
    ],
    "interview_closings": [
        "In an interview, I would show that I can design and commission HVAC systems using sound load calculations, airflow control, and verification evidence.",
    ],
    "contamination_terms": ["contraindications", "case record trail", "SBAR", "allergen"],
}
