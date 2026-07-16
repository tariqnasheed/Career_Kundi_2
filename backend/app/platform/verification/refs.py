"""Verification domain reference errors (0053-F9). Pure Python — no DB/API."""

from __future__ import annotations


class VerificationRefError(ValueError):
    """Invalid review state, actor, or transition input."""
