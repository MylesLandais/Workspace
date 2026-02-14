# RunPod Deployment Risk Registry

This document tracks known risks, failures, and mitigation strategies for RunPod serverless deployments.

## Risk Categories

### Build Infrastructure Risks

#### RISK-001: Registry Push Failure After Successful Build

**Status:** ACTIVE  
**Severity:** HIGH  
**Probability:** MEDIUM  
**First Observed:** 2025-12-19 00:31:58 UTC  
**Latest Occurrence:** 2025-12-19 03:36:32 UTC  
**Build IDs:** `5ced0749-36eb-4f7a-870f-9549c2cd743c`, `60893f8c-1670-49f5-a84d-ceb389ac1d3a`, `6f76c1e6-e98e-4875-97b2-1f2133e1802d`

**Description:**
**WHAT WE FIXED:** Changed CUDA from 13.1.0 (doesn't exist) to 12.8.1 (verified exists). This fixed the build - it now completes successfully.

**REMAINING ISSUE:** After successful build, registry push fails with:
```
Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present
Image push finished with wrong exit code
```

**Correlation with RISK-002:**
Analysis of build logs shows a pattern where layer locking errors (RISK-002) precede registry push failures. Specifically, layer `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` consistently shows locking errors (760ms - 1.3s duration) immediately before push failure. This suggests the layer locking may be a contributing factor or symptom of the underlying infrastructure issue.

**Impact:**
- Build appears successful but image is not deployed
- Wastes build time (30+ minutes)
- No clear error indication to user
- Deployment appears stuck
- Pattern recurrence indicates systemic infrastructure issue

**Root Cause:**
RunPod infrastructure issue - build artifacts not found for registry push. Possible causes:
1. Buildkit layer export process fails to complete artifact preparation
2. Concurrent build contention causing artifact corruption
3. Registry service unable to access build output directory

**Mitigation:**
1. Monitor build logs for registry push errors
2. Track layer locking patterns and correlation with push failures
3. Implement retry mechanism for failed pushes
4. Add GitHub Actions step to verify deployment after release
5. Document in troubleshooting guide (see `RUNPOD_TROUBLESHOOTING.md`)
6. Contact RunPod support with pattern analysis

**Workaround:**
- Manually retry build in RunPod console
- Wait 5-10 minutes between retry attempts to avoid contention
- Monitor for layer locking errors in logs before retry

**Related Build Logs:**
- `/home/warby/Downloads/build-logs-5ced0749-36eb-4f7a-870f-9549c2cd743c.txt` (lines 382-395)
- Build log from 2025-12-19 19:24:58 UTC (layer locking + push failure pattern)
- `/home/warby/Downloads/build-logs-6f76c1e6-e98e-4875-97b2-1f2133e1802d.txt` (lines 452-496): 40 layer locking errors, max duration 1.47s, followed by registry push failure

---

#### RISK-002: Docker Layer Locking Errors

**Status:** ACTIVE  
**Severity:** MEDIUM  
**Probability:** MEDIUM (increasing with pattern observation)  
**First Observed:** 2025-12-19 00:31:57 UTC  
**Latest Occurrence:** 2025-12-19 03:36:32 UTC  
**Build IDs:** `5ced0749-36eb-4f7a-870f-9549c2cd743c`, `60893f8c-1670-49f5-a84d-ceb389ac1d3a`, `6f76c1e6-e98e-4875-97b2-1f2133e1802d`

**Description:**
Multiple RPC errors during layer export:
```
ERROR: (*service).Write failed: rpc error: code = Unavailable desc = 
ref layer-sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef locked for 760ms-1.3s: unavailable
```

**Correlation with RISK-001:**
Analysis shows this layer locking consistently occurs immediately before registry push failures. The specific layer `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` appears in multiple failed builds with lock durations of 172µs up to 1.3 seconds. This suggests the locking may prevent proper artifact finalization, leading to missing registry push artifacts.

**Impact:**
- Build may appear to hang during export
- Transient errors that may not resolve
- **Correlated with registry push failures (RISK-001)**
- Indicates infrastructure contention or resource exhaustion

**Root Cause:**
Concurrent access to Docker layers during export. Buildkit infrastructure contention, possibly exacerbated by:
1. Large layer sizes (12.48GB+ model downloads before mitigation)
2. Concurrent builds on shared infrastructure
3. Registry service unable to acquire layer locks in time

**Mitigation:**
- Monitor layer hash patterns in failed builds
- Track lock duration and frequency
- Document correlation with push failures for RunPod support
- Consider image size optimizations to reduce layer contention

**Workaround:**
- Retry build if locking errors exceed 2 seconds
- Space out build attempts to reduce infrastructure contention
- Monitor for specific layer hashes that consistently fail

---

### CUDA Version Risks

#### RISK-003: Invalid CUDA Version Tags

**Status:** RESOLVED  
**Severity:** HIGH  
**Probability:** LOW  
**First Observed:** 2025-12-18  
**Build ID:** `cb34a015-5202-408c-898e-4d3a0f97ccc3`

**Description:**
Build failed with:
```
ERROR: nvidia/cuda:13.1.0-cudnn-runtime-ubuntu24.04: not found
```

**Impact:**
- Complete build failure
- Wasted build time
- Blocked deployments

**Root Cause:**
CUDA 13.1.0 does not exist. Incorrect version recommendation.

**Resolution:**
- Updated to `nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04`
- Verified tag exists on Docker Hub
- Documented in `RUNPOD_DEPLOYMENT.md`

**Prevention:**
- Always verify CUDA tags exist before updating Dockerfile
- Check Docker Hub: https://hub.docker.com/r/nvidia/cuda/tags
- Use RunPod recommended versions (12.8 for ComfyUI)

---

#### RISK-004: CUDA Version Mismatch (Runtime vs Devel)

**Status:** MITIGATED  
**Severity:** MEDIUM  
**Probability:** LOW  
**Date Identified:** 2025-12-18

**Description:**
Confusion between `-runtime` and `-devel` variants. Devel images larger, runtime preferred for production.

**Impact:**
- Larger image sizes if wrong variant used
- Longer build times
- Unnecessary dependencies

**Mitigation:**
- Use `-runtime` variant for production (`Dockerfile.runpod`)
- Document variant selection criteria
- Verify on Docker Hub before committing

**Current State:**
Using `12.8.1-cudnn-runtime-ubuntu24.04` (correct)

---

### Custom Node Installation Risks

#### RISK-005: Missing Custom Nodes in Production

**Status:** RESOLVED  
**Severity:** HIGH  
**Probability:** LOW  
**First Observed:** 2025-12-18

**Description:**
Workflow execution failed with:
```
Cannot execute because node NanoBananaAIO does not exist
```

**Impact:**
- Production workflows fail
- Inconsistent dev/prod environments

**Root Cause:**
Node installed locally but not in `Dockerfile.runpod`.

**Resolution:**
- Added `ComfyUI_Nano_Banana` to Dockerfile
- Synced all custom nodes across environments
- Documented node list in worklog

**Prevention:**
- Maintain node manifest in repository
- Validate node installations in CI/CD
- Test workflows before deployment

---

### Configuration Risks

#### RISK-006: Manual Configuration Errors

**Status:** ACTIVE  
**Severity:** MEDIUM  
**Probability:** HIGH  
**Date Identified:** 2025-12-18

**Description:**
RunPod console configuration prone to human error:
- Wrong branch selected
- Missing CUDA version filter
- Network volume not attached
- Missing environment variables

**Impact:**
- Failed deployments
- Misconfigured endpoints
- Wasted time debugging

**Mitigation:**
- Document all required settings in `RUNPOD_DEPLOYMENT.md`
- Create configuration checklist
- Future: Infrastructure as Code (see `TODO.md`)

**Prevention:**
- [ ] Automate endpoint configuration (Terraform/Pulumi)
- [ ] Version control endpoint configs
- [ ] Configuration validation scripts

---

#### RISK-007: Missing Network Volume Mount

**Status:** ACTIVE  
**Severity:** HIGH  
**Probability:** MEDIUM  
**Date Identified:** 2025-12-18

**Description:**
Network volume not attached to endpoint, causing model loading failures.

**Impact:**
- Workers cannot access models
- Workflow execution failures
- Cold start delays

**Mitigation:**
- Document volume attachment in deployment guide
- Add to configuration checklist
- Future: Automate volume provisioning

---

#### RISK-008: Missing Environment Variables

**Status:** ACTIVE  
**Severity:** HIGH  
**Probability:** MEDIUM  
**Date Identified:** 2025-12-18

**Description:**
Required environment variables not set in RunPod console:
- `GOOGLE_API_KEY` (required for Nano Banana)

**Impact:**
- Node functionality fails
- API calls rejected
- Workflow errors

**Mitigation:**
- Document in `RUNPOD_DEPLOYMENT.md`
- Add to configuration checklist
- Future: Automated secret injection

---

### Build Performance Risks

#### RISK-009: Slow Custom Node Installation

**Status:** ACTIVE  
**Severity:** LOW  
**Probability:** HIGH  
**Build ID:** `5ced0749-36eb-4f7a-870f-9549c2cd743c`

**Description:**
Custom node installations take 90-215 seconds each due to ComfyRegistry data fetching.

**Impact:**
- Long build times (30+ minutes total)
- High build costs
- Slow iteration cycles

**Observed Times:**
- ComfyUI-GGUF: ~95s
- RES4LYF: ~106s
- comfy-image-saver: ~94s
- VibeVoice + IndexTTS2: ~215s
- ComfyUI_Nano_Banana: ~108s

**Mitigation:**
- Acceptable for production builds
- Consider caching strategies if builds become problematic
- Monitor for regressions

**Optimization Ideas:**
- Pre-build base images with common nodes
- Use Docker layer caching more effectively
- Parallel node installations (if supported)

---

## Risk Prioritization

### Critical (Fix Immediately)

1. **RISK-001**: Registry Push Failure - Blocks deployments
2. **RISK-003**: Invalid CUDA Versions - Complete build failure (RESOLVED)

### High Priority (Address Soon)

3. **RISK-006**: Manual Config Errors - Frequent issues
4. **RISK-007**: Missing Network Volume - Deployment failure
5. **RISK-008**: Missing Environment Variables - Runtime failures

### Medium Priority (Monitor)

6. **RISK-002**: Layer Locking Errors - Non-fatal but concerning
7. **RISK-004**: CUDA Variant Confusion - Mitigated

### Low Priority (Acceptable)

8. **RISK-009**: Slow Build Times - Acceptable for now

---

## Risk Review Schedule

- **Weekly:** Review active risks during sprint planning
- **After Each Build Failure:** Add new risks or update existing
- **Quarterly:** Full risk registry review and cleanup

---

## Related Documents

- `RUNPOD_DEPLOYMENT.md` - Deployment configuration
- `TODO.md` - Infrastructure automation roadmap
- `251218-worklog.md` - Session worklogs with error details

---

*Last Updated: 2025-12-19 03:36:32 UTC*

