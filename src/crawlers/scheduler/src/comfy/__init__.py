"""Comfy workflows interface package.

This package will expose a simple, modular interface for running ComfyUI workflows
from notebooks or other callers. Keep implementations small and well-documented.
"""

# Make the package importable even before client is fully implemented
try:
    from .client import ComfyClient
    __all__ = ["ComfyClient"]
except Exception:
    __all__ = []
