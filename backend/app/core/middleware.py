"""
core/middleware.py
=======================
Backward-compatible request middleware entrypoint.

PF10-S1 moved correlation / completion logging into
`app.platform.observability.middleware.ObservabilityMiddleware`.
This module re-exports that middleware under the historical name so
existing imports keep working.
"""

from app.platform.observability.middleware import (
    ObservabilityMiddleware as RequestContextMiddleware,
)

__all__ = ["RequestContextMiddleware"]
