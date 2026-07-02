from __future__ import annotations

DEFAULT_PACK = {
    "verification_checks": [
        "check task output against defined scope",
        "verify required records are complete",
        "confirm controls were executed in sequence",
    ],
    "safety_checks": [
        "identify immediate risk conditions before execution",
        "escalate unresolved risks promptly",
    ],
    "common_mistakes": [
        "Skipping documented checks under time pressure.",
        "Assuming completion without verification evidence.",
    ],
}
