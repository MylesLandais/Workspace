# RunPod Deployment Risk Registry

This document tracks known risks, failures, and mitigation strategies for RunPod serverless deployments.

## Risk Categories

### Build Infrastructure Risks

#### RISK-001: Registry Push Failure After Successful Build

**Status:** ACTIVE  
**Severity:** HIGH  
**Probability:** MEDIUM  
**First Observed:** 2025-12-19  
**Build ID:** `5ced0749-36eb-4f7a-870f-9549c2cd743c`

**Description:**
Build completes successfully but registry push fails with:
```
Error: neither /app/registry-push/output.tar found nor /app/registry-push/.output-image/index.json present
Image push finished with wrong exit code
```

**Impact:**
- Build appears successful but image is not deployed
- Wastes build time (30+ minutes)
- No clear error indication to user
- Deployment appears stuck

**Root Cause:**
RunPod infrastructure issue - build artifacts not found for registry push. This is an external dependency failure, not a code issue.

**Mitigation:**
1. Monitor build logs for registry push errors
2. Implement retry mechanism for failed pushes
3. Add GitHub Actions step to verify deployment after release
4. Document as known issue in troubleshooting guide

**Workaround:**
- Manually retry build in RunPod console
- Contact RunPod support if persistent

**Related Build Logs:**
- `/home/warby/Downloads/build-logs-5ced0749-36eb-4f7a-870f-9549c2cd743c.txt` (lines 382-395)

---

#### RISK-002: Docker Layer Locking Errors

**Status:** ACTIVE  
**Severity:** MEDIUM  
**Probability:** LOW  
**First Observed:** 2025-12-19  
**Build ID:** `5ced0749-36eb-4f7a-870f-9549c2cd743c`

**Description:**
Multiple RPC errors during layer export:
```
ERROR: (*service).Write failed: rpc error: code = Unavailable desc = 
ref layer-sha256:... locked for Xµs/ms: unavailable
```

**Impact:**
- Build may appear to hang
- Transient errors that typically resolve
- May contribute to registry push failures

**Root Cause:**
Concurrent access to Docker layers during export. Buildkit infrastructure contention.

**Mitigation:**
- These are warnings, build typically continues
- Monitor if frequency increases
- Consider build timeouts if persistent

**Workaround:**
- None required - errors are non-fatal
- Retry if build fails completely

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

*Last Updated: 2025-12-19*

