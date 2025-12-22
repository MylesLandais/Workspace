# Infrastructure as Code TODOs

**PRIORITY: P0 - CRITICAL**  
**See RISK_REGISTRY.md for full risk assessment**

## RunPod Build Configuration Issues

### Critical Build Errors (from build logs)

**RISK-001: Invalid CUDA Version** - CRITICAL  
**RISK-002: Registry Push Failure** - CRITICAL  
**RISK-005: Missing Infrastructure Config** - HIGH

1. **Invalid CUDA Version**
   - Error: `nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04: not found`
   - Fix: CUDA 13.1.0 doesn't exist. Use valid version (12.1.0, 12.4.0, 12.6.0, or 11.8.0)
   - TODO: Add CUDA version validation to build config

2. **Wrong Git Branch**
   - Currently using: `feature/runpod-worker`
   - TODO: Add git branch configuration to deployment config

3. **Missing Network Volume Mount**
   - TODO: Add network_volume_id to build configuration

4. **Missing Datacenter Selection**
   - TODO: Add datacenter_id to build configuration

5. **Dockerfile Path Configuration**
   - Currently hardcoded: `Dockerfile.runpod`
   - TODO: Make dockerfile_path and build_context configurable

## Implementation Tasks

### 1. Extend `src/infra/runpod_config.py`

Add `BuildConfig` dataclass:

```python
@dataclass
class BuildConfig:
    cuda_version: str  # Validated against known versions
    git_repo: str
    git_branch: str = "main"
    dockerfile_path: str = "Dockerfile.runpod"
    build_context: str = "."
    network_volume_id: Optional[str] = None
    datacenter_id: Optional[str] = None
```

Add CUDA version validation:

```python
VALID_CUDA_VERSIONS = [
    "11.8.0", "12.1.0", "12.4.0", "12.6.0", "12.8.0"
]

def validate_cuda_version(version: str) -> bool:
    return version in VALID_CUDA_VERSIONS
```

### 2. Extend `src/infra/runpod_manager.py`

Add method for custom builds:

```python
def build_and_deploy_custom_image(
    self,
    name: str,
    build_config: BuildConfig,
    **overrides
) -> Dict[str, Any]:
    """Build custom image and deploy pod."""
    # Validate CUDA version
    if not validate_cuda_version(build_config.cuda_version):
        raise ValueError(f"Invalid CUDA version: {build_config.cuda_version}")
    
    # Build image with proper config
    # Deploy pod with network volume and datacenter
    pass
```

### 3. Create Deployment Config Files

Create `config/runpod_deployments/comfyui-custom-build.yaml`:

```yaml
build_config:
  cuda_version: "12.6.0"
  git_repo: "https://github.com/MylesLandais/ComfyUI"
  git_branch: "main"  # or correct branch
  dockerfile_path: "Dockerfile.runpod"
  build_context: "."
  network_volume_id: "${RUNPOD_NETWORK_VOLUME_ID}"
  datacenter_id: "US-1"  # or appropriate datacenter

deployment:
  gpu: "NVIDIA RTX 3090"
  volume_in_gb: 100
  ports: "8188/tcp"
```

### 4. Update DEFAULT_DEPLOYMENT_CONFIGS

Add build_config field to existing configs to support both pre-built images and custom builds.

### 5. Fix Registry Push Failure (RISK-002)

**CRITICAL:** Build completes but image push fails.

**Investigation needed:**
- Verify buildkit export paths match RunPod expectations
- Check if output.tar or index.json are created in correct location
- Add post-build validation to ensure artifacts exist before push

**Implementation:**
- Add artifact validation step after build
- Implement retry logic for registry push
- Add logging for push failure diagnostics

