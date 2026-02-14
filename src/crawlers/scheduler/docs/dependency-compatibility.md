# Dependency Compatibility Reference

## Overview

This document outlines critical dependency version requirements to prevent import errors, particularly with `pydantic` and `typing_extensions` compatibility.

## Common Issues

### Issue 1: typing_extensions/pydantic Compatibility

**Error**: `ImportError: cannot import name 'Sentinel' from 'typing_extensions'`

**Root Cause**: `pydantic-core` requires `typing_extensions>=4.5.0` for the `Sentinel` type, but older versions may be installed in Docker containers or base images.

### Issue 2: google.adk Module Not Found

**Error**: `ModuleNotFoundError: No module named 'google.adk'`

**Root Cause**: `google-genai` version is too old. The `google.adk` module requires `google-genai>=1.16.1`.

## Required Dependencies

The following packages must meet minimum version requirements:

| Package | Minimum Version | Constraint | Purpose |
|---------|----------------|------------|---------|
| `google-genai` | 1.16.1 | `>=1.16.1` | Required for `google.adk` module (Agent Development Kit) |
| `typing_extensions` | 4.5.0 | `>=4.5.0` | Required for `pydantic-core` Sentinel type |
| `pydantic` | 2.0.0 | `>=2.0.0,<3.0.0` | Core validation library |
| `pydantic-core` | 2.0.0 | `>=2.0.0` | Core dependency of pydantic |
| `Pillow` | 10.0.0 | `>=10.0.0` | Image processing (used by runpod_runner) |

## Dependency Chains

```
google-genai (>=1.16.1) → google.adk module
litellm → pydantic → pydantic-core → typing_extensions (>=4.5.0)
```

## Configuration Files

Both `requirements.txt` and `pyproject.toml` must include these constraints:

**requirements.txt**:
```txt
google-genai>=1.16.1
typing_extensions>=4.5.0
pydantic>=2.0.0,<3.0.0
pydantic-core>=2.0.0
Pillow>=10.0.0
```

**pyproject.toml**:
```toml
dependencies = [
    "google-genai>=1.16.1",
    "typing_extensions>=4.5.0",
    "pydantic>=2.0.0,<3.0.0",
    "pydantic-core>=2.0.0",
    "Pillow>=10.0.0",
]
```

## Resolution

### Docker Container

```bash
# Update google-genai first (required for ADK)
pip install --upgrade google-genai>=1.16.1

# Then update other dependencies
pip install --upgrade typing_extensions>=4.5.0 pydantic>=2.0.0 pydantic-core>=2.0.0 Pillow>=10.0.0
```

Or reinstall from requirements:

```bash
pip install -r requirements.txt --upgrade
```

### Verification

```python
# Test google.adk import
from google.adk.runners import Runner
from google.adk.agents import Agent
print("✓ google.adk module available")

# Test pydantic compatibility
import litellm
from pydantic import BaseModel
print("✓ Dependencies correctly installed")
```

## Prevention Guidelines

1. **Pin critical dependencies** with explicit version constraints in `requirements.txt`
2. **Use version ranges** for compatibility (e.g., `pydantic>=2.0.0,<3.0.0`)
3. **Test imports** in Docker container before deployment
4. **Check for conflicts** using `pip check` after installation

## Related Packages

This issue commonly affects projects using:
- `litellm` (LLM abstraction layer)
- `fastapi` (web framework)
- Any package depending on `pydantic` v2.x

## Additional Notes

- Docker base images may include outdated packages; always verify versions
- `pydantic` v2.x introduced breaking changes requiring newer `typing_extensions`
- The `Sentinel` type was added in `typing_extensions` 4.5.0

