"""RunPod helper module for shelling out to runpodctl.

This module provides a tiny `RunpodClient` which builds runpodctl commands,
supports dry-run mode and returns structured results. It's intentionally small
so it can be used from notebooks and higher-level orchestration code.
"""

from .client import RunpodClient
