# RunPod Build Risk Registry

**Last Updated:** 2025-12-19  
**Status:** 2 CRITICAL risks identified, 1 partially mitigated (RISK-001)

## Risk Severity Levels

- **CRITICAL**: Blocks all builds, must fix immediately
- **HIGH**: Causes build failures, needs urgent attention
- **MEDIUM**: Causes warnings/retries, should fix soon
- **LOW**: Minor issues, can be addressed later

---

## CRITICAL RISKS

### RISK-001: Invalid CUDA Version Configuration
**Severity:** CRITICAL  
**Status:** MITIGATED (validation added, still needs deployment)  
**First Observed:** 2025-12-18  
**Build Log:** `build-logs-cb34a015-5202-408c-898e-4d3a0f97ccc3.txt`

**Error:**
```
ERROR: docker.io/nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04: not found
failed to solve: nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04: failed to resolve source metadata
```

**Root Cause:**
- CUDA version 13.1.0 does not exist
- Valid CUDA versions: 11.8.0, 12.1.0, 12.4.0, 12.6.0, 12.8.0
- No validation in build configuration

**Impact:**
- 100% build failure rate
- All custom image builds fail immediately

**Mitigation Implemented:**
1. ✅ Added `VALID_CUDA_VERSIONS` constant to `src/infra/runpod_config.py`
2. ✅ Created `validate_cuda_version()` function
3. ✅ Added `BuildConfig` dataclass with auto-validation in `__post_init__`
4. ✅ Default CUDA version set to 12.6.0 in example configs

**Remaining Work:**
- Deploy validation to production builds
- Update existing build configurations to use BuildConfig
- Add validation to RunPod UI workflows (if applicable)

**Priority:** P0 - Validation implemented, needs deployment

---

### RISK-002: Registry Push Failure
**Severity:** CRITICAL  
**Status:** OPEN  
**First Observed:** 2025-12-19  
**Build Log:** `build-logs-5ced0749-36eb-4f7a-870f-9549c2cd743c.txt`

**Error:**
```
Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present
Image push finished with wrong exit code
```

**Root Cause:**
- Build completes successfully but image export fails
- Missing output artifacts in expected paths
- Registry push service cannot find build artifacts

**Impact:**
- Builds complete but images are not pushed to registry
- Cannot deploy built images
- Wasted build time and resources

**Mitigation:**
1. Investigate buildkit export configuration
2. Verify output paths match RunPod registry push expectations
3. Add post-build validation to ensure artifacts exist
4. Implement retry logic for registry push

**Priority:** P0 - Fix immediately

---

## HIGH RISKS

### RISK-003: Missing Git in Build Environment
**Severity:** HIGH  
**Status:** OPEN  
**First Observed:** 2025-12-18

**Error:**
```
WARNING: current commit information was not captured by the build: git was not found in the system: exec: "git": executable file not found in $PATH
```

**Root Cause:**
- Git not installed in buildkit container
- Cannot capture commit metadata for builds
- Affects build reproducibility and tracking

**Impact:**
- No commit information in build metadata
- Difficult to track which code version was built
- Reduced build traceability

**Mitigation:**
1. Ensure git is installed in base build image
2. Add git to Dockerfile.runpod if using custom base
3. Capture commit hash as build arg

**Priority:** P1 - Fix this week

---

### RISK-004: Layer Locking During Cache Export
**Severity:** HIGH  
**Status:** OPEN  
**First Observed:** 2025-12-19

**Error:**
```
ERROR: (*service).Write failed: rpc error: code = Unavailable desc = ref layer-sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef locked for Xms: unavailable
```

**Root Cause:**
- Concurrent access to same Docker layer during cache export
- Buildkit layer locking mechanism conflicts
- Multiple retries eventually succeed but cause delays

**Impact:**
- Build cache export takes longer
- Potential for cache corruption
- Unpredictable build times

**Mitigation:**
1. Investigate buildkit cache export configuration
2. Add retry logic with exponential backoff
3. Consider sequential cache export for critical builds
4. Monitor for cache corruption

**Priority:** P1 - Fix this week

---

### RISK-005: Missing Infrastructure Configuration
**Severity:** HIGH  
**Status:** MITIGATED (infrastructure-as-code implemented)  
**First Observed:** 2025-12-18

**Issues:**
1. Wrong Git branch (using `feature/runpod-worker` instead of correct branch)
2. Missing network volume mount configuration
3. Missing datacenter selection
4. Hardcoded Dockerfile path

**Root Cause:**
- No infrastructure-as-code for build configuration
- Manual configuration errors
- No validation of deployment settings

**Impact:**
- Builds use wrong code branch
- No persistent storage mounted
- Suboptimal datacenter selection
- Cannot easily change Dockerfile location

**Mitigation Implemented:**
1. ✅ Created `BuildConfig` dataclass in `src/infra/runpod_config.py`
   - Fields: git_repo, git_branch, network_volume_id, datacenter_id, dockerfile_path, build_context
2. ✅ Added `build_and_deploy_custom_image()` method to RunPodManager
3. ✅ Created `config/runpod_deployments/comfyui-custom-build.yaml` example
4. ✅ Added `comfyui-custom-build` to DEFAULT_DEPLOYMENT_CONFIGS

**Remaining Work:**
- Update existing build workflows to use BuildConfig
- Document datacenter selection best practices
- Add network volume validation

**Priority:** P1 - Infrastructure-as-code complete, needs adoption

---

## MEDIUM RISKS

### RISK-006: ComfyRegistry Cache Update Delays
**Severity:** MEDIUM  
**Status:** OPEN  
**First Observed:** 2025-12-19

**Warning:**
```
[ComfyUI-Manager] The ComfyRegistry cache update is still in progress, so an outdated cache is being used.
```

**Root Cause:**
- ComfyUI-Manager registry cache updates are slow
- Builds proceed with stale cache data
- May install wrong versions of custom nodes

**Impact:**
- Potential for installing outdated custom nodes
- Slower build times while waiting for cache
- Inconsistent builds if cache updates mid-build

**Mitigation:**
1. Pre-warm ComfyRegistry cache before builds
2. Add cache staleness check
3. Wait for cache update completion if critical

**Priority:** P2 - Fix next sprint

---

## Risk Summary

| Risk ID | Severity | Status | Priority |
|---------|----------|--------|----------|
| RISK-001 | CRITICAL | MITIGATED | P0 |
| RISK-002 | CRITICAL | OPEN | P0 |
| RISK-003 | HIGH | OPEN | P1 |
| RISK-004 | HIGH | OPEN | P1 |
| RISK-005 | HIGH | MITIGATED | P1 |
| RISK-006 | MEDIUM | OPEN | P2 |

**Total Critical:** 2 (1 mitigated, 1 open)  
**Total High:** 3 (1 mitigated, 2 open)  
**Total Medium:** 1 (open)

**Progress:** 2 risks mitigated, 4 remaining

---

## Action Items

### Immediate (P0 - Today)
1. Fix CUDA version validation (RISK-001)
2. Investigate and fix registry push failure (RISK-002)

### This Week (P1)
1. Add git to build environment (RISK-003)
2. Fix layer locking issues (RISK-004)
3. Implement infrastructure-as-code (RISK-005)

### Next Sprint (P2)
1. Optimize ComfyRegistry cache handling (RISK-006)

---

## Notes

- All build logs should be archived for analysis
- Consider implementing automated build health monitoring
- Add pre-build validation checks to catch issues early
- Create runbook for common build failures



