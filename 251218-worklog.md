# Worklog: RunPod Custom Node Sync and CUDA Fix

## Session Metadata

| Field | Value |
|-------|-------|
| Date | 2025-12-18 |
| Duration | Multiple sessions |
| Engineer | AI Assistant |
| Branch | `feature/runpod-worker` |
| Status | In Progress |

## Session 2: Custom Node Sync and CUDA Upgrade

### Session Metadata

| Field | Value |
|-------|-------|
| Session id | 251218-2218 |
| Date | 2025-12-18 |
| Duration | ~30 minutes |
| Engineer | AI Assistant |
| Branch | `feature/runpod-worker` |
| Status | Completed |

### Problem Statement

Workflow execution failed on RunPod with missing node error:

```
Job failed: Cannot execute because node NanoBananaAIO does not exist.
Node ID: '#38'
```

Additionally, local Docker container failed to start:

```
nvidia-container-cli: requirement error: unsatisfied condition: cuda>=12.6,
please update your driver to a newer version, or use an earlier cuda container
```

### Root Cause Analysis

| Issue | Cause | Impact |
|-------|-------|--------|
| Missing `NanoBananaAIO` | Node only installed locally, not in `Dockerfile.runpod` | RunPod workers cannot execute workflows using Nano Banana |
| Local CUDA mismatch | Host GPU driver older than container CUDA requirement | Local dev container fails to start (separate from RunPod) |

The custom node list in `Dockerfile.runpod` was incomplete:

**Before (Lines 84-91):**
```dockerfile
RUN comfy-node-install https://github.com/city96/ComfyUI-GGUF
RUN comfy-node-install https://github.com/rgthree/rgthree-comfy
RUN comfy-node-install https://github.com/ClownsharkBatwing/RES4LYF
RUN comfy-node-install https://github.com/giriss/comfy-image-saver
RUN comfy-node-install https://github.com/Enemyx-net/VibeVoice-ComfyUI && \
    GIT_LFS_SKIP_SMUDGE=1 comfy-node-install https://github.com/snicolast/ComfyUI-IndexTTS2
# MISSING: ComfyUI_Nano_Banana
```

---

### Changes Made

#### 1. CUDA Base Image Upgrade (Later Fixed in Session 3)

Updated `Dockerfile.runpod` line 2:

```dockerfile
# Before
ARG BASE_IMAGE=nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04

# After (Initially tried 13.1.0, but this doesn't exist - fixed in Session 3)
ARG BASE_IMAGE=nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04
```

**Note:** CUDA 13.1.0 doesn't exist - this was corrected in Session 3.

#### 2. Added Nano Banana Custom Node

Added to `Dockerfile.runpod` after line 91:

```dockerfile
RUN comfy-node-install https://github.com/ru4ls/ComfyUI_Nano_Banana
```

#### 3. Documented API Key Requirement

Updated `runpod.env.example`:

```
RUNPOD_API_KEY=your_api_key_here
RUNPOD_ENDPOINT_ID=jx1jkdf7ozhpmm
GOOGLE_API_KEY=your_google_api_key_here  # NEW - Required for Nano Banana
```

#### 4. Security: Added .env to .gitignore

Prevents accidental commit of secrets.

#### 5. CI/CD Workflow

Created `.github/workflows/runpod-build.yml`:
- Validates `Dockerfile.runpod` syntax with hadolint
- Checks all required files exist before build
- Optional RunPod endpoint status monitoring
- Triggers on pushes to `feature/runpod-worker`

---

### Commits Created

```
c0c3ab9c [RUNPOD-4] Add GitHub Actions workflow for RunPod build validation
f04cdc5f [RUNPOD-3] Upgrade CUDA to 13.1.0 and add Nano Banana node
```

---

### Updated Custom Node List

| Node | Repository | Status |
|------|------------|--------|
| ComfyUI-GGUF | city96 | Existing |
| rgthree-comfy | rgthree | Existing |
| RES4LYF | ClownsharkBatwing | Existing |
| comfy-image-saver | giriss | Existing |
| VibeVoice-ComfyUI | Enemyx-net | Existing |
| ComfyUI-IndexTTS2 | snicolast | Existing |
| **ComfyUI_Nano_Banana** | **ru4ls** | **NEW** |

---

*Session completed: 2025-12-18 22:18 UTC*

---

## Session 3: CUDA Version Fix and Deployment Documentation

### Session Metadata

| Field | Value |
|-------|-------|
| Session id | 251218-2330 |
| Date | 2025-12-18 |
| Duration | ~15 minutes |
| Engineer | AI Assistant |
| Branch | `feature/runpod-worker` |
| Status | Ready for Push & Release |

### Problem Statement

Build failed with:
```
ERROR: nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04: not found
```

**Root Cause:** CUDA 13.1.0 does not exist as a Docker image. Previous recommendation was incorrect.

**Build ID:** `cb34a015-5202-408c-898e-4d3a0f97ccc3`

### Solution

Changed to **CUDA 12.8.1** (latest available, recommended for ComfyUI per RunPod docs):

```dockerfile
# BROKEN - 13.1.0 doesn't exist
ARG BASE_IMAGE=nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04

# FIXED - Use 12.8.1 (verified on Docker Hub)
ARG BASE_IMAGE=nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04
```

**Reference:** [RunPod CUDA Version Selection](https://docs.runpod.io/serverless/endpoints/endpoint-configurations#cuda-version-selection)

### Additional Issues Identified

Manual RunPod console configuration prone to errors:
- Wrong branch selected (`master` instead of `feature/runpod-worker`)
- Missing CUDA version filter configuration
- Network volume not attached
- Datacenter restrictions
- Missing environment variables

### Changes Made

#### 1. Fixed CUDA Version

Updated `Dockerfile.runpod` line 2 to use `12.8.1-cudnn-runtime-ubuntu24.04`.

#### 2. Created Deployment Documentation

**File:** `RUNPOD_DEPLOYMENT.md`

Includes:
- GitHub repository configuration (branch, Dockerfile path)
- GPU selection (32GB PRO / 24GB PRO fallback)
- CUDA version filter: `>=12.4` (all newer for compatibility)
- Worker scaling recommendations
- Environment variables (`GOOGLE_API_KEY`)
- Network volume configuration
- Troubleshooting guide

#### 3. Created Infrastructure-as-Code TODO

**File:** `TODO.md`

Tracks future automation:
- RunPod endpoint configuration via Terraform/Pulumi
- Secrets management (GOOGLE_API_KEY)
- Network volume provisioning
- Multi-environment support (dev/staging/prod)
- Monitoring and alerting integration

#### 4. Enhanced CI/CD Workflow

Updated `.github/workflows/runpod-build.yml`:
- Auto-creates GitHub releases after validation
- RunPod watches releases (not commits) for rebuilds
- Release format: `runpod-YYYYMMDD-HHMMSS`

### Commits Created

```
c16ca09f [RUNPOD-7] Fix CUDA version and add deployment documentation
5921f98e [RUNPOD-6] Add RunPod monitoring script for CI/CD pipeline
487afb39 [RUNPOD-5] Add auto-release to trigger RunPod rebuilds
```

### Next Steps

1. **Push commits** to `origin/feature/runpod-worker`
2. **GitHub Actions** will auto-create release (runpod-YYYYMMDD-HHMMSS)
3. **RunPod** detects release and rebuilds endpoint
4. **Verify** build succeeds with CUDA 12.8.1
5. **Test** workflow execution with Nano Banana node

### RunPod Console Configuration Checklist

Before rebuild, verify in RunPod console:
- [ ] Branch: `feature/runpod-worker`
- [ ] Dockerfile Path: `Dockerfile.runpod`
- [ ] Build Context: `.`
- [ ] GPU: 32GB PRO (4090) + 24GB PRO fallback
- [ ] CUDA Version Filter: `>=12.4` (select all compatible)
- [ ] Network Volume: (attach your volume ID)
- [ ] Environment: `GOOGLE_API_KEY` set

---

*Session completed: 2025-12-18 23:30 UTC*

---

## Session 4: Build Infrastructure Failure Analysis and Risk Registry

### Session Metadata

| Field | Value |
|-------|-------|
| Session id | 251219-0045 |
| Date | 2025-12-19 |
| Duration | ~20 minutes |
| Engineer | AI Assistant |
| Branch | `feature/runpod-worker` |
| Status | Documentation Complete |

### Problem Statement

Build ID `5ced0749-36eb-4f7a-870f-9549c2cd743c` appeared to succeed but deployment failed.

**Analysis:**
- Docker build completed successfully
- All custom nodes installed (including Nano Banana)
- Image export completed
- **Registry push failed:** `Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present`

This is a **RunPod infrastructure failure**, not a code issue.

### Errors Identified

1. **Registry Push Failure (RISK-001)** - CRITICAL
   - Build completes but image not deployed
   - No clear error indication
   - Blocks deployments

2. **Docker Layer Locking Errors (RISK-002)** - MEDIUM
   - Multiple RPC unavailable errors during export
   - Non-fatal but concerning
   - May contribute to push failures

### Changes Made

#### 1. Created Risk Registry

**File:** `RISK_REGISTRY.md`

Comprehensive risk tracking document including:
- 9 identified risks (build infrastructure, CUDA, nodes, configuration)
- Risk prioritization (Critical/High/Medium/Low)
- Mitigation strategies
- Reference to build logs and related issues

#### 2. Updated TODO Priorities

**File:** `TODO.md`

Added **Critical Priority** section for RISK-001:
- Immediate actions for registry push failures
- Monitoring and retry mechanisms
- Long-term infrastructure reliability improvements

#### 3. Documented All Known Issues

Tracked risks include:
- Registry push failures (ACTIVE, CRITICAL)
- CUDA version issues (RESOLVED)
- Missing custom nodes (RESOLVED)
- Manual configuration errors (ACTIVE)
- Missing network volumes (ACTIVE)
- Missing environment variables (ACTIVE)
- Build performance (ACCEPTABLE)

### Risk Prioritization

**Critical:**
- RISK-001: Registry Push Failure (blocks deployments)

**High:**
- RISK-006: Manual Config Errors
- RISK-007: Missing Network Volume
- RISK-008: Missing Environment Variables

**Resolved:**
- RISK-003: Invalid CUDA Version (fixed: 12.8.1)
- RISK-005: Missing Custom Nodes (added Nano Banana)

### Next Steps

1. Monitor for registry push failures
2. Implement build verification in CI/CD
3. Add retry mechanisms for failed builds
4. Contact RunPod support if persistent
5. Continue IaC automation to reduce manual config errors

### Build Log Reference

- `/home/warby/Downloads/build-logs-5ced0749-36eb-4f7a-870f-9549c2cd743c.txt`
- Errors at lines 382-395

---

*Session completed: 2025-12-19 00:45 UTC*

