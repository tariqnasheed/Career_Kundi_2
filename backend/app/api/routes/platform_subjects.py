"""
Compatibility shim — PF3 subject routes live in platform.py (0050-PF8-S1).

Kept so historical imports of `platform_subjects` still resolve to the
platform router surface.
"""

from app.api.routes.platform import router

__all__ = ["router"]
